from abc import ABC, abstractmethod
from enum import Enum
from typing import Generic, TypeVar, Union


class ConstraintType(Enum):  # TODO add remaining ones
    Tag = 0
    TagID = 1
    MediaType = 2
    FileType = 3
    Path = 4

    @staticmethod
    def from_string(text: str) -> "ConstraintType":
        return {
            "tag": ConstraintType.Tag,
            "tag_id": ConstraintType.TagID,
            "mediatype": ConstraintType.MediaType,
            "filetype": ConstraintType.FileType,
            "path": ConstraintType.Path,
        }.get(text.lower(), None)


class AST:
    parent: "AST" = None

    def __str__(self):
        class_name = self.__class__.__name__
        fields = vars(self)  # Get all instance variables as a dictionary
        field_str = ", ".join(f"{key}={value}" for key, value in fields.items())
        return f"{class_name}({field_str})"

    def __repr__(self) -> str:
        return self.__str__()


class ANDList(AST):
    terms: list[Union["ORList", "Constraint"]]

    def __init__(self, terms: list[Union["ORList", "Constraint"]]) -> None:
        super().__init__()
        for term in terms:
            term.parent = self
        self.terms = terms


class ORList(AST):
    elements: list[ANDList]

    def __init__(self, elements: list[ANDList]) -> None:
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


T = TypeVar("T")


class BaseVisitor(ABC, Generic[T]):
    def visit(self, node: AST) -> T:
        return {
            ANDList: self.visit_and_list,
            ORList: self.visit_or_list,
            Constraint: self.visit_constraint,
            Property: self.visit_property,
        }[type(node)](node)

    @abstractmethod
    def visit_and_list(self, node: ANDList) -> T:
        raise NotImplementedError()

    @abstractmethod
    def visit_or_list(self, node: ORList) -> T:
        raise NotImplementedError()

    @abstractmethod
    def visit_constraint(self, node: Constraint) -> T:
        raise NotImplementedError()

    @abstractmethod
    def visit_property(self, node: Property) -> T:
        raise NotImplementedError()
