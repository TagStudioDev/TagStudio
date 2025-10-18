# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import re
from typing import TYPE_CHECKING, override

import structlog
from sqlalchemy import ColumnElement, and_, distinct, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import ilike_op

from tagstudio.core.library.alchemy.constants import TAG_CHILDREN_ID_QUERY
from tagstudio.core.library.alchemy.joins import TagEntry
from tagstudio.core.library.alchemy.models import Entry, Tag, TagAlias
from tagstudio.core.media_types import FILETYPE_EQUIVALENTS, MediaCategories
from tagstudio.core.query_lang.ast import (
    AST,
    ANDList,
    BaseVisitor,
    Constraint,
    ConstraintType,
    Not,
    ORList,
    Property,
)

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library
else:
    Library = None  # don't import library because of circular imports

logger = structlog.get_logger(__name__)


def get_filetype_equivalency_list(item: str) -> list[str] | set[str]:
    for s in FILETYPE_EQUIVALENTS:
        if item in s:
            return s
    return [item]


class SQLBoolExpressionBuilder(BaseVisitor[ColumnElement[bool]]):
    def __init__(self, lib: Library) -> None:
        super().__init__()
        self.lib = lib

    @override
    def visit_or_list(self, node: ORList) -> ColumnElement[bool]:  # type: ignore
        tag_ids, bool_expressions = self.__separate_tags(node.elements, only_single=False)
        if len(tag_ids) > 0:
            bool_expressions.append(self.__entry_has_any_tags(tag_ids))
        return or_(*bool_expressions)

    @override
    def visit_and_list(self, node: ANDList) -> ColumnElement[bool]:  # type: ignore
        tag_ids, bool_expressions = self.__separate_tags(node.terms, only_single=True)
        if len(tag_ids) > 0:
            bool_expressions.append(self.__entry_has_all_tags(tag_ids))
        return and_(*bool_expressions)

    @override
    def visit_constraint(self, node: Constraint) -> ColumnElement[bool]:  # type: ignore
        """Returns a Boolean Expression that is true, if the Entry satisfies the constraint."""
        if len(node.properties) != 0:
            raise NotImplementedError("Properties are not implemented yet")  # TODO TSQLANG

        if node.type == ConstraintType.Tag:
            return self.__entry_has_any_tags(self.__get_tag_ids(node.value))
        elif node.type == ConstraintType.TagID:
            return self.__entry_has_any_tags([int(node.value)])
        elif node.type == ConstraintType.Path:
            ilike = False
            glob = False

            # Smartcase check
            if node.value == node.value.lower():
                ilike = True
            if node.value.startswith("*") or node.value.endswith("*"):
                glob = True

            if ilike and glob:
                logger.info("ConstraintType.Path", ilike=True, glob=True)
                return func.lower(Entry.path).op("GLOB")(f"{node.value.lower()}")
            elif ilike:
                logger.info("ConstraintType.Path", ilike=True, glob=False)
                return ilike_op(Entry.path, f"%{node.value}%")
            elif glob:
                logger.info("ConstraintType.Path", ilike=False, glob=True)
                return Entry.path.op("GLOB")(node.value)
            else:
                logger.info(
                    "ConstraintType.Path", ilike=False, glob=False, re=re.escape(node.value)
                )
                return Entry.path.regexp_match(re.escape(node.value))
        elif node.type == ConstraintType.MediaType:
            extensions: set[str] = set[str]()
            for media_cat in MediaCategories.ALL_CATEGORIES:
                if node.value == media_cat.name:
                    extensions = extensions | media_cat.extensions
                    break
            return Entry.suffix.in_(map(lambda x: x.replace(".", ""), extensions))
        elif node.type == ConstraintType.FileType:
            return or_(
                *[Entry.suffix.ilike(ft) for ft in get_filetype_equivalency_list(node.value)]
            )
        elif node.type == ConstraintType.Special:  # noqa: SIM102 unnecessary once there is a second special constraint
            if node.value.lower() == "untagged":
                return ~Entry.id.in_(select(Entry.id).join(TagEntry))

        # raise exception if Constraint stays unhandled
        raise NotImplementedError("This type of constraint is not implemented yet")

    @override
    def visit_property(self, node: Property) -> ColumnElement[bool]:  # type: ignore
        raise NotImplementedError("This should never be reached!")

    @override
    def visit_not(self, node: Not) -> ColumnElement[bool]:  # type: ignore
        return ~self.visit(node.child)

    def __get_tag_ids(self, tag_name: str, include_children: bool = True) -> list[int]:
        """Given a tag name find the ids of all tags that this name could refer to."""
        with Session(self.lib.engine) as session:
            tag_ids = list(
                session.scalars(
                    select(Tag.id)
                    .where(or_(Tag.name.ilike(tag_name), Tag.shorthand.ilike(tag_name)))
                    .union(select(TagAlias.tag_id).where(TagAlias.name.ilike(tag_name)))
                )
            )
            if len(tag_ids) > 1:
                logger.debug(
                    f'Tag Constraint "{tag_name}" is ambiguous, {len(tag_ids)} matching tags found',
                    tag_ids=tag_ids,
                    include_children=include_children,
                )
            if not include_children:
                return tag_ids
            outp: list[int] = []
            for tag_id in tag_ids:
                outp.extend(list(session.scalars(TAG_CHILDREN_ID_QUERY, {"tag_id": tag_id})))
            return outp

    def __separate_tags(
        self, terms: list[AST], only_single: bool = True
    ) -> tuple[list[int], list[ColumnElement[bool]]]:
        tag_ids: set[int] = set()
        bool_expressions: list[ColumnElement[bool]] = []

        for term in terms:
            if isinstance(term, Constraint) and len(term.properties) == 0:
                match term.type:
                    case ConstraintType.TagID:
                        try:
                            tag_ids.add(int(term.value))
                        except ValueError:
                            logger.error(
                                "[SQLBoolExpressionBuilder] Could not cast value to an int Tag ID",
                                value=term.value,
                            )
                        continue
                    case ConstraintType.Tag:
                        ids = self.__get_tag_ids(term.value)
                        if not only_single:
                            tag_ids.update(ids)
                            continue
                        elif len(ids) == 1:
                            tag_ids.add(ids[0])
                            continue
                    case ConstraintType.FileType:
                        pass
                    case ConstraintType.Path:
                        pass
                    case ConstraintType.Special:
                        pass
                    case _:
                        raise NotImplementedError(f"Unhandled constraint: '{term.type}'")

            bool_expressions.append(self.visit(term))
        return list(tag_ids), bool_expressions

    def __entry_has_all_tags(self, tag_ids: list[int]) -> ColumnElement[bool]:
        """Returns Binary Expression that is true if the Entry has all provided tag ids."""
        # Relational Division Query
        return Entry.id.in_(
            select(TagEntry.entry_id)
            .where(TagEntry.tag_id.in_(tag_ids))
            .group_by(TagEntry.entry_id)
            .having(func.count(distinct(TagEntry.tag_id)) == len(tag_ids))
        )

    def __entry_has_any_tags(self, tag_ids: list[int]) -> ColumnElement[bool]:
        """Returns Binary Expression that is true if the Entry has any of the provided tag ids."""
        return Entry.id.in_(
            select(TagEntry.entry_id).where(TagEntry.tag_id.in_(tag_ids)).distinct()
        )
