from typing import TYPE_CHECKING

import structlog
from sqlalchemy import ColumnElement, and_, distinct, func, or_, select, text
from sqlalchemy.orm import Session
from src.core.media_types import FILETYPE_EQUIVALENTS, MediaCategories
from src.core.query_lang import BaseVisitor
from src.core.query_lang.ast import ANDList, Constraint, ConstraintType, Not, ORList, Property

from .joins import TagField
from .models import Entry, Tag, TagAlias, TagBoxField

# workaround to have autocompletion in the Editor
if TYPE_CHECKING:
    from .library import Library
else:
    Library = None  # don't import .library because of circular imports

logger = structlog.get_logger(__name__)

CHILDREN_QUERY = text("""
-- Note for this entire query that tag_subtags.child_id is the parent id and tag_subtags.parent_id is the child id due to bad naming
WITH RECURSIVE Subtags AS (
    SELECT :tag_id AS child_id
    UNION ALL
    SELECT ts.parent_id AS child_id
	FROM tag_subtags ts
    INNER JOIN Subtags s ON ts.child_id = s.child_id
)
SELECT * FROM Subtags;
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

        # Search for TagID / unambigous Tag Constraints and store the respective tag ids seperately
        for term in node.terms:
            if isinstance(term, Constraint) and len(term.properties) == 0:
                match term.type:
                    case ConstraintType.TagID:
                        tag_ids.append(int(term.value))
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
                self.__entry_satisfies_expression(TagField.tag_id == tag_ids[0])
            )

        return and_(*bool_expressions)

    def visit_constraint(self, node: Constraint) -> ColumnElement[bool]:
        if len(node.properties) != 0:
            raise NotImplementedError("Properties are not implemented yet")  # TODO TSQLANG

        if node.type == ConstraintType.Tag:
            return self.__entry_matches_tag_ids(self.__get_tag_ids(node.value))
        elif node.type == ConstraintType.TagID:
            return self.__entry_matches_tag_ids([int(node.value)])
        elif node.type == ConstraintType.Path:
            return Entry.path.op("GLOB")(node.value)
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
                return ~Entry.id.in_(
                    select(Entry.id).join(Entry.tag_box_fields).join(TagBoxField.tags)
                )

        # raise exception if Constraint stays unhandled
        raise NotImplementedError("This type of constraint is not implemented yet")

    def visit_property(self, node: Property) -> None:
        raise NotImplementedError("This should never be reached!")

    def visit_not(self, node: Not) -> ColumnElement[bool]:
        return ~self.visit(node.child)

    def __entry_matches_tag_ids(self, tag_ids: list[int]) -> ColumnElement[bool]:
        """Returns a boolean expression that is true if the entry has at least one of the supplied tags."""  # noqa: E501
        return (
            select(1)
            .correlate(TagBoxField)
            .where(and_(TagField.field_id == TagBoxField.id, TagField.tag_id.in_(tag_ids)))
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
                outp.extend(list(session.scalars(CHILDREN_QUERY, {"tag_id": tag_id})))
            return outp

    def __entry_has_all_tags(self, tag_ids: list[int]) -> ColumnElement[bool]:
        """Returns Binary Expression that is true if the Entry has all provided tag ids."""
        # Relational Division Query
        # The changes to this technically introduce a bug
        # which occurs when the tags are split across multiple tag box fields,
        # but since those will be removed soon the bug will also disappear soon
        # (also this method isn't used in every query that has an AND,
        #  so the bug doesn't even have that many chances to rear its ugly head)
        return TagBoxField.id.in_(
            select(TagField.field_id)
            .where(TagField.tag_id.in_(tag_ids))
            .group_by(TagField.field_id)
            .having(func.count(distinct(TagField.tag_id)) == len(tag_ids))
        )

    def __entry_satisfies_expression(self, expr: ColumnElement[bool]) -> ColumnElement[bool]:
        """Returns Binary Expression that is true if the Entry satisfies the column expression."""
        return Entry.id.in_(
            select(Entry.id).outerjoin(Entry.tag_box_fields).outerjoin(TagField).where(expr)
        )
