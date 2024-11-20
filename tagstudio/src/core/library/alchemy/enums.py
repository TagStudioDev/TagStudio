import enum
from dataclasses import dataclass
from pathlib import Path


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


class SearchMode(enum.IntEnum):
    """Operational modes for item searching."""

    AND = 0
    OR = 1


class ItemType(enum.Enum):
    ENTRY = 0
    COLLATION = 1
    TAG_GROUP = 2


@dataclass
class FilterState:
    """Represent a state of the Library grid view."""

    # these should remain
    page_index: int | None = None
    page_size: int | None = None
    search_mode: SearchMode = SearchMode.AND  # TODO - actually implement this

    # these should be erased on update
    # tag name
    tag: str | None = None
    # tag ID
    tag_id: int | None = None

    # entry id
    id: int | None = None
    # whole path
    path: Path | str | None = None
    # file name
    name: str | None = None
    # file type
    filetype: str | None = None
    mediatype: str | None = None

    # a generic query to be parsed
    query: str | None = None

    def __post_init__(self):
        # strip values automatically
        if query := (self.query and self.query.strip()):
            # parse the value
            if ":" in query:
                kind, _, value = query.partition(":")
                value = value.replace('"', "")
            else:
                # default to tag search
                kind, value = "tag", query

            if kind == "tag_id":
                self.tag_id = int(value)
            elif kind == "tag":
                self.tag = value
            elif kind == "path":
                self.path = value
            elif kind == "name":
                self.name = value
            elif kind == "id":
                self.id = int(self.id) if str(self.id).isnumeric() else self.id
            elif kind == "filetype":
                self.filetype = value
            elif kind == "mediatype":
                self.mediatype = value

        else:
            self.tag = self.tag and self.tag.strip()
            self.tag_id = int(self.tag_id) if str(self.tag_id).isnumeric() else self.tag_id
            self.path = self.path and str(self.path).strip()
            self.name = self.name and self.name.strip()
            self.id = int(self.id) if str(self.id).isnumeric() else self.id

        if self.page_index is None:
            self.page_index = 0
        if self.page_size is None:
            self.page_size = 500

    @property
    def summary(self):
        """Show query summary."""
        return self.query or self.tag or self.name or self.tag_id or self.path or self.id

    @property
    def limit(self):
        return self.page_size

    @property
    def offset(self):
        return self.page_size * self.page_index


class FieldTypeEnum(enum.Enum):
    TEXT_LINE = "Text Line"
    TEXT_BOX = "Text Box"
    TAGS = "Tags"
    DATETIME = "Datetime"
    BOOLEAN = "Checkbox"
