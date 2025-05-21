# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import re
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import ColumnElement, and_, distinct, func, or_, select, text
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import ilike_op

from tagstudio.core.library.alchemy.joins import TagEntry
from tagstudio.core.library.alchemy.models import Entry, Tag, TagAlias
from tagstudio.core.media_types import FILETYPE_EQUIVALENTS, MediaCategories
from tagstudio.core.query_lang.ast import (
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

# TODO: Reevaluate after subtags -> parent tags name change
TAG_CHILDREN_ID_QUERY = text("""
-- Note for this entire query that tag_parents.child_id is the parent id and tag_parents.parent_id is the child id due to bad naming
WITH RECURSIVE ChildTags AS (
    SELECT :tag_id AS child_id
    UNION
    SELECT tp.parent_id AS child_id
	FROM tag_parents tp
    INNER JOIN ChildTags c ON tp.child_id = c.child_id
)
SELECT child_id FROM ChildTags;
""")  # noqa: E501


def get_filetype_equivalency_list(item: str) -> list[str] | set[str]:
    for s in FILETYPE_EQUIVALENTS:
        if item in s:
            return s
    return [item]


class SQLBoolExpressionBuilder(BaseVisitor[ColumnElement[bool]]):
    def __init__(self, lib: Library) -> None:
        super().__init__()
        self.lib = lib

    def visit_or_list(self, node: ORList) -> ColumnElement[bool]:
        return or_(*[self.visit(element) for element in node.elements])

    def visit_and_list(self, node: ANDList) -> ColumnElement[bool]:
        tag_ids: list[int] = []
        bool_expressions: list[ColumnElement[bool]] = []

        # Search for TagID / unambiguous Tag Constraints and store the respective tag ids separately
        for term in node.terms:
            if isinstance(term, Constraint) and len(term.properties) == 0:
                match term.type:
                    case ConstraintType.TagID:
                        try:
                            tag_ids.append(int(term.value))
                        except ValueError:
                            logger.error(
                                "[SQLBoolExpressionBuilder] Could not cast value to an int Tag ID",
                                value=term.value,
                            )
                        continue
                    case ConstraintType.Tag:
                        if len(ids := self.__get_tag_ids(term.value)) == 1:
                            tag_ids.append(ids[0])
                            continue

            bool_expressions.append(self.visit(term))

        # If there are at least two tag ids use a relational division query
        # to efficiently check all of them
        if len(tag_ids) > 1:
            bool_expressions.append(self.__entry_has_all_tags(tag_ids))
        # If there is just one tag id, check the normal way
        elif len(tag_ids) == 1:
            bool_expressions.append(
                self.__entry_satisfies_expression(TagEntry.tag_id == tag_ids[0])
            )

        return and_(*bool_expressions)

    def visit_constraint(self, node: Constraint) -> ColumnElement[bool]:
        """Returns a Boolean Expression that is true, if the Entry satisfies the constraint."""
        if len(node.properties) != 0:
            raise NotImplementedError("Properties are not implemented yet")  # TODO TSQLANG

        if node.type == ConstraintType.Tag:
            return self.__entry_matches_tag_ids(self.__get_tag_ids(node.value))
        elif node.type == ConstraintType.TagID:
            return self.__entry_matches_tag_ids([int(node.value)])
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

    def visit_property(self, node: Property) -> ColumnElement[bool]:
        raise NotImplementedError("This should never be reached!")

    def visit_not(self, node: Not) -> ColumnElement[bool]:
        return ~self.visit(node.child)

    def __entry_matches_tag_ids(self, tag_ids: list[int]) -> ColumnElement[bool]:
        """Returns a boolean expression that is true if the entry has at least one of the supplied tags."""  # noqa: E501
        return (
            select(1)
            .correlate(Entry)
            .where(and_(TagEntry.entry_id == Entry.id, TagEntry.tag_id.in_(tag_ids)))
            .exists()
        )

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
            outp = []
            for tag_id in tag_ids:
                outp.extend(list(session.scalars(TAG_CHILDREN_ID_QUERY, {"tag_id": tag_id})))
            return outp

    def __entry_has_all_tags(self, tag_ids: list[int]) -> ColumnElement[bool]:
        """Returns Binary Expression that is true if the Entry has all provided tag ids."""
        # Relational Division Query
        return Entry.id.in_(
            select(TagEntry.entry_id)
            .where(TagEntry.tag_id.in_(tag_ids))
            .group_by(TagEntry.entry_id)
            .having(func.count(distinct(TagEntry.tag_id)) == len(tag_ids))
        )

    def __entry_satisfies_expression(self, expr: ColumnElement[bool]) -> ColumnElement[bool]:
        """Returns Binary Expression that is true if the Entry satisfies the column expression.

        Executed on: Entry ⟕ TagEntry (Entry LEFT OUTER JOIN TagEntry).
        """
        return Entry.id.in_(select(Entry.id).outerjoin(TagEntry).where(expr))
