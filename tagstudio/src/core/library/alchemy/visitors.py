from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import ColumnExpressionArgument
from src.core.media_types import MediaCategories
from src.core.query_lang import BaseVisitor
from src.core.query_lang.ast import ANDList, Constraint, ConstraintType, ORList, Property

from .models import Entry, Tag, TagAlias


class SQLBoolExpressionBuilder(BaseVisitor):
    def visit_or_list(self, node: ORList) -> ColumnExpressionArgument:
        return or_(*[self.visit(element) for element in node.elements])

    def visit_and_list(self, node: ANDList) -> ColumnExpressionArgument:
        return and_(*[self.visit(term) for term in node.terms])

    def visit_constraint(self, node: Constraint) -> ColumnExpressionArgument:
        if len(node.properties) != 0:
            raise NotImplementedError("Properties are not implemented yet")  # TODO TSQLANG

        if node.type == ConstraintType.Tag:
            return or_(
                Tag.name.ilike(node.value),
                Tag.shorthand.ilike(node.value),
                TagAlias.name.ilike(node.value),
                aliased(Tag).name.ilike(node.value),
            )
        elif node.type == ConstraintType.TagID:
            return Tag.id == int(node.value)
        elif node.type == ConstraintType.Path:
            return Entry.path.ilike(node.value.replace("*", "%"))  # TODO TSQLANG this is broken
        elif node.type == ConstraintType.MediaType:
            extensions: set[str] = set[str]()
            for media_cat in MediaCategories.ALL_CATEGORIES:
                if node.value == media_cat.name:
                    extensions = extensions | media_cat.extensions
                    break
            return Entry.suffix.in_(
                map(lambda x: x.replace(".", ""), extensions)
            )  # TODO audio doesn't work on mp3 files (might be my library)
        elif node.type == ConstraintType.FileType:
            return Entry.suffix.ilike(
                node.value
            )  # TODO TSQLANG this is broken for mp3, but works for png (might be my library)

        raise NotImplementedError("This type of constraint is not implemented yet")

    def visit_property(self, node: Property) -> None:
        return
