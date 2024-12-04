from typing import TYPE_CHECKING

from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import BinaryExpression, ColumnExpressionArgument
from src.core.media_types import MediaCategories
from src.core.query_lang import BaseVisitor
from src.core.query_lang.ast import AST, ANDList, Constraint, ConstraintType, Not, ORList, Property

from .joins import TagField
from .models import Entry, Tag, TagAlias, TagBoxField

# workaround to have autocompletion in the Editor
if TYPE_CHECKING:
    from .library import Library
else:
    Library = None  # don't import .library because of circular imports


class SQLBoolExpressionBuilder(BaseVisitor[ColumnExpressionArgument]):
    def __init__(self, lib: Library) -> None:
        super().__init__()
        self.lib = lib

    def visit_or_list(self, node: ORList) -> ColumnExpressionArgument:
        return or_(*[self.visit(element) for element in node.elements])

    def visit_and_list(self, node: ANDList) -> ColumnExpressionArgument:
        tag_ids: list[int] = []
        bool_expressions: list[ColumnExpressionArgument] = []

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

            bool_expressions.append(self.__entry_satisfies_ast(term))

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

    def visit_constraint(self, node: Constraint) -> ColumnExpressionArgument:
        if len(node.properties) != 0:
            raise NotImplementedError("Properties are not implemented yet")  # TODO TSQLANG

        if node.type == ConstraintType.Tag:
            return TagBoxField.tags.any(Tag.id.in_(self.__get_tag_ids(node.value)))
        elif node.type == ConstraintType.TagID:
            return TagBoxField.tags.any(Tag.id == int(node.value))
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
            return Entry.suffix.ilike(node.value)
        elif node.type == ConstraintType.Special:  # noqa: SIM102 unnecessary once there is a second special constraint
            if node.value.lower() == "untagged":
                return ~Entry.id.in_(
                    select(Entry.id).join(Entry.tag_box_fields).join(TagBoxField.tags)
                )

        # raise exception if Constraint stays unhandled
        raise NotImplementedError("This type of constraint is not implemented yet")

    def visit_property(self, node: Property) -> None:
        raise NotImplementedError("This should never be reached!")

    def visit_not(self, node: Not) -> ColumnExpressionArgument:
        return ~self.__entry_satisfies_ast(node.child)

    def __get_tag_ids(self, tag_name: str) -> list[int]:
        """Given a tag name find the ids of all tags that this name could refer to."""
        with Session(self.lib.engine, expire_on_commit=False) as session:
            return list(
                session.scalars(
                    select(Tag.id)
                    .where(or_(Tag.name.ilike(tag_name), Tag.shorthand.ilike(tag_name)))
                    .union(select(TagAlias.tag_id).where(TagAlias.name.ilike(tag_name)))
                )
            )

    def __entry_has_all_tags(self, tag_ids: list[int]) -> BinaryExpression[bool]:
        """Returns Binary Expression that is true if the Entry has all provided tag ids."""
        # Relational Division Query
        return Entry.id.in_(
            select(Entry.id)
            .outerjoin(TagBoxField)
            .outerjoin(TagField)
            .where(TagField.tag_id.in_(tag_ids))
            .group_by(Entry.id)
            .having(func.count(distinct(TagField.tag_id)) == len(tag_ids))
        )

    def __entry_satisfies_ast(self, partial_query: AST) -> BinaryExpression[bool]:
        """Returns Binary Expression that is true if the Entry satisfies the partial query."""
        return self.__entry_satisfies_expression(self.visit(partial_query))

    def __entry_satisfies_expression(
        self, expr: ColumnExpressionArgument
    ) -> BinaryExpression[bool]:
        """Returns Binary Expression that is true if the Entry satisfies the column expression."""
        return Entry.id.in_(
            select(Entry.id).outerjoin(Entry.tag_box_fields).outerjoin(TagField).where(expr)
        )
