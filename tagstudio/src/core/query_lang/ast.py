from enum import Enum
from typing import Union


class ConstraintType(Enum):
    Tag = 0
    MediaType = 1

    @staticmethod
    def from_string(text: str) -> "ConstraintType":
        return {
            "tag": ConstraintType.Tag,
            "mediatype": ConstraintType.MediaType
        }.get(text.lower(), None)

class AST:
    def __str__(self):
        class_name = self.__class__.__name__
        fields = vars(self)  # Get all instance variables as a dictionary
        field_str = ", ".join(f"{key}={value}" for key, value in fields.items())
        return f"{class_name}({field_str})"
    
    def __repr__(self) -> str:
        return self.__str__()

class ANDList(AST):
    elements: list["ORList"]

    def __init__(self, elements: list["ORList"]) -> None:
        super().__init__()
        self.elements = elements

class ORList(AST):
    terms: list[Union[ANDList, "Constraint"]]

    def __init__(self, terms: list[Union[ANDList, "Constraint"]]) -> None:
        super().__init__()
        self.terms = terms

class Constraint(AST):
    type: ConstraintType
    value: str
    properties: list["Property"]

    def __init__(self, type: ConstraintType, value: str, properties: list["Property"]) -> None:
        super().__init__()
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