import enum
from dataclasses import dataclass, replace
from pathlib import Path

from src.core.query_lang import AST as Query  # noqa: N811
from src.core.query_lang import Constraint, ConstraintType, Parser


class TagColor(enum.IntEnum):
    DEFAULT = 1
    BLACK = 2
    DARK_GRAY = 3
    GRAY = 4
    LIGHT_GRAY = 5
    WHITE = 6
    LIGHT_PINK = 7
    PINK = 8
    RED = 9
    RED_ORANGE = 10
    ORANGE = 11
    YELLOW_ORANGE = 12
    YELLOW = 13
    LIME = 14
    LIGHT_GREEN = 15
    MINT = 16
    GREEN = 17
    TEAL = 18
    CYAN = 19
    LIGHT_BLUE = 20
    BLUE = 21
    BLUE_VIOLET = 22
    VIOLET = 23
    PURPLE = 24
    LAVENDER = 25
    BERRY = 26
    MAGENTA = 27
    SALMON = 28
    AUBURN = 29
    DARK_BROWN = 30
    BROWN = 31
    LIGHT_BROWN = 32
    BLONDE = 33
    PEACH = 34
    WARM_GRAY = 35
    COOL_GRAY = 36
    OLIVE = 37

    @staticmethod
    def get_color_from_str(color_name: str) -> "TagColor":
        for color in TagColor:
            if color.name == color_name.upper().replace(" ", "_"):
                return color
        return TagColor.DEFAULT


class ItemType(enum.Enum):
    ENTRY = 0
    COLLATION = 1
    TAG_GROUP = 2


@dataclass
class FilterState:
    """Represent a state of the Library grid view."""

    # these should remain
    page_index: int | None = 0
    page_size: int | None = 500

    # these should be erased on update
    # Abstract Syntax Tree Of the current Search Query
    ast: Query = None

    @property
    def limit(self):
        return self.page_size

    @property
    def offset(self):
        return self.page_size * self.page_index

    @classmethod
    def show_all(cls) -> "FilterState":
        return FilterState()

    @classmethod
    def from_search_query(cls, search_query: str) -> "FilterState":
        return cls(ast=Parser(search_query).parse())

    @classmethod
    def from_tag_id(cls, tag_id: int | str) -> "FilterState":
        return cls(ast=Constraint(ConstraintType.TagID, str(tag_id), []))

    @classmethod
    def from_path(cls, path: Path | str) -> "FilterState":
        return cls(ast=Constraint(ConstraintType.Path, str(path).strip(), []))

    @classmethod
    def from_mediatype(cls, mediatype: str) -> "FilterState":
        return cls(ast=Constraint(ConstraintType.MediaType, mediatype, []))

    @classmethod
    def from_filetype(cls, filetype: str) -> "FilterState":
        return cls(ast=Constraint(ConstraintType.FileType, filetype, []))

    @classmethod
    def from_tag_name(cls, tag_name: str) -> "FilterState":
        return cls(ast=Constraint(ConstraintType.Tag, tag_name, []))

    def with_page_size(self, page_size: int) -> "FilterState":
        return replace(self, page_size=page_size)


class FieldTypeEnum(enum.Enum):
    TEXT_LINE = "Text Line"
    TEXT_BOX = "Text Box"
    TAGS = "Tags"
    DATETIME = "Datetime"
    BOOLEAN = "Checkbox"
