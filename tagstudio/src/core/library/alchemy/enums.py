import enum
from dataclasses import dataclass, field
from enum import Enum, auto


class TagColor(Enum):
    default = 1
    black = 2
    dark_gray = 3
    gray = 4
    light_gray = 5
    white = 6
    light_pink = 7
    pink = 8
    red = 9
    red_orange = 10
    orange = 11
    yellow_orange = 12
    yellow = 13
    lime = 14
    light_green = 15
    mint = 16
    green = 17
    teal = 18
    cyan = 19
    light_blue = 20
    blue = 21
    blue_violet = 22
    violet = 23
    purple = 24
    lavender = 25
    berry = 26
    magenta = 27
    salmon = 28
    auburn = 29
    dark_brown = 30
    brown = 31
    light_brown = 32
    blonde = 33
    peach = 34
    warm_gray = 35
    cool_gray = 36
    olive = 37


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

    page_index: int = 0
    page_size: int = 100
    name: str | None = None
    id: int | None = None
    tag_id: int | None = None
    search_mode: SearchMode = SearchMode.AND  # TODO - actually implement this

    # default_search: str = "name"

    def __post_init__(self):
        # strip query automatically
        self.name = self.name and self.name.strip()
        self.id = self.id and int(self.id)
        self.tag_id = self.tag_id and int(self.tag_id)

    @property
    def summary(self) -> str | int | None:
        """Show query summary"""
        return self.name or self.id or None

    @property
    def limit(self):
        return self.page_size

    @property
    def offset(self):
        return self.page_size * self.page_index
