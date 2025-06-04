from abc import ABC, abstractmethod
from enum import Enum
from typing import Generic, TypeVar, Union


class ConstraintType(Enum):
    Tag = 0
    TagID = 1
    MediaType = 2
    FileType = 3
    Path = 4
    Special = 5

    @staticmethod
    def from_string(text: str) -> Union["ConstraintType", None]:
        return {
            "tag": ConstraintType.Tag,
            "tag_id": ConstraintType.TagID,
            "mediatype": ConstraintType.MediaType,
            "filetype": ConstraintType.FileType,
            "path": ConstraintType.Path,
            "special": ConstraintType.Special,
        }.get(text.lower(), None)


class AST:
    parent: Union["AST", None] = None

    def __str__(self):
        class_name = self.__class__.__name__
        fields = vars(self)  # Get all instance variables as a dictionary
        field_str = ", ".join(f"{key}={value}" for key, value in fields.items())
        return f"{class_name}({field_str})"

    def __repr__(self) -> str:
        return self.__str__()


class ANDList(AST):
    terms: list[AST]

    def __init__(self, terms: list[AST]) -> None:
        super().__init__()
        for term in terms:
            term.parent = self
        self.terms = terms


class ORList(AST):
    elements: list[AST]

    def __init__(self, elements: list[AST]) -> None:
        super().__init__()
        for element in elements:
            element.parent = self
        self.elements = elements


class Constraint(AST):
    type: ConstraintType
    value: str
    properties: list["Property"]

    def __init__(self, type: ConstraintType, value: str, properties: list["Property"]) -> None:
        super().__init__()
        for prop in properties:
            prop.parent = self
        self.type = type
        self.value = value
        self.properties = properties


class Property(AST):
    key: str
    value: str

    def __init__(self, key: str, value: str) -> None:
        super().__init__()
        self.key = key
        self.value = value


class Not(AST):
    child: AST

    def __init__(self, child: AST) -> None:
        super().__init__()
        self.child = child


T = TypeVar("T")


class BaseVisitor(ABC, Generic[T]):
    def visit(self, node: AST) -> T:
        if isinstance(node, ANDList):
            return self.visit_and_list(node)
        elif isinstance(node, ORList):
            return self.visit_or_list(node)
        elif isinstance(node, Constraint):
            return self.visit_constraint(node)
        elif isinstance(node, Property):
            return self.visit_property(node)
        elif isinstance(node, Not):
            return self.visit_not(node)
        raise Exception(f"Unknown Node Type of {node}")  # pragma: nocover

    @abstractmethod
    def visit_and_list(self, node: ANDList) -> T:
        raise NotImplementedError()  # pragma: nocover

    @abstractmethod
    def visit_or_list(self, node: ORList) -> T:
        raise NotImplementedError()  # pragma: nocover

    @abstractmethod
    def visit_constraint(self, node: Constraint) -> T:
        raise NotImplementedError()  # pragma: nocover

    @abstractmethod
    def visit_property(self, node: Property) -> T:
        raise NotImplementedError()  # pragma: nocover

    @abstractmethod
    def visit_not(self, node: Not) -> T:
        raise NotImplementedError()  # pragma: nocover
