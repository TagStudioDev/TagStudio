from typing import TYPE_CHECKING

import structlog
from sqlalchemy import and_, distinct, func, or_, select, text
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import BinaryExpression, ColumnExpressionArgument
from src.core.media_types import FILETYPE_EQUIVALENTS, MediaCategories
from src.core.query_lang import BaseVisitor
from src.core.query_lang.ast import AST, ANDList, Constraint, ConstraintType, Not, ORList, Property

from .joins import TagEntry
from .models import Entry, Tag, TagAlias

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


class SQLBoolExpressionBuilder(BaseVisitor[ColumnExpressionArgument]):
    def __init__(self, lib: Library) -> None:
        super().__init__()
        self.lib = lib

    def visit_or_list(self, node: ORList) -> ColumnExpressionArgument:
        return or_(*[self.visit(element) for element in node.elements])

    def visit_and_list(self, node: ANDList) -> ColumnExpressionArgument:
        tag_ids: list[int] = []
        bool_expressions: list[ColumnExpressionArgument] = []

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

            bool_expressions.append(self.__entry_satisfies_ast(term))

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

    def visit_constraint(self, node: Constraint) -> ColumnExpressionArgument:
        """Returns a Boolean Expression that is true, if the Entry satisfies the constraint."""
        if len(node.properties) != 0:
            raise NotImplementedError("Properties are not implemented yet")  # TODO TSQLANG

        if node.type == ConstraintType.Tag:
            return Entry.tags.any(Tag.id.in_(self.__get_tag_ids(node.value)))
        elif node.type == ConstraintType.TagID:
            return Entry.tags.any(Tag.id == int(node.value))
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
                return ~Entry.id.in_(select(Entry.id).join(TagEntry))

        # raise exception if Constraint stays unhandled
        raise NotImplementedError("This type of constraint is not implemented yet")

    def visit_property(self, node: Property) -> None:
        raise NotImplementedError("This should never be reached!")

    def visit_not(self, node: Not) -> ColumnExpressionArgument:
        return ~self.__entry_satisfies_ast(node.child)

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

    def __entry_has_all_tags(self, tag_ids: list[int]) -> BinaryExpression[bool]:
        """Returns Binary Expression that is true if the Entry has all provided tag ids."""
        # Relational Division Query
        return Entry.id.in_(
            select(Entry.id)
            .outerjoin(TagEntry)
            .where(TagEntry.tag_id.in_(tag_ids))
            .group_by(Entry.id)
            .having(func.count(distinct(TagEntry.tag_id)) == len(tag_ids))
        )

    def __entry_satisfies_ast(self, partial_query: AST) -> BinaryExpression[bool]:
        """Returns Binary Expression that is true if the Entry satisfies the partial query."""
        return self.__entry_satisfies_expression(self.visit(partial_query))

    def __entry_satisfies_expression(
        self, expr: ColumnExpressionArgument
    ) -> BinaryExpression[bool]:
        """Returns Binary Expression that is true if the Entry satisfies the column expression.

        Executed on: Entry ⟕ TagEntry (Entry LEFT OUTER JOIN TagEntry).
        """
        return Entry.id.in_(select(Entry.id).outerjoin(TagEntry).where(expr))
