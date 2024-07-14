import enum
from dataclasses import dataclass


class SettingItems(str, enum.Enum):
    """List of setting item names."""

    START_LOAD_LAST = "start_load_last"
    LAST_LIBRARY = "last_library"
    LIBS_LIST = "libs_list"
    WINDOW_SHOW_LIBS = "window_show_libs"
    AUTOPLAY = "autoplay_videos"


class Theme(str, enum.Enum):
    COLOR_BG = "#65000000"
    COLOR_HOVER = "#65AAAAAA"
    COLOR_PRESSED = "#65EEEEEE"
    COLOR_DISABLED = "#65F39CAA"
    COLOR_DISABLED_BG = "#65440D12"


class FieldID(int, enum.Enum):
    TITLE = 0
    AUTHOR = 1
    ARTIST = 2
    DESCRIPTION = 4
    NOTES = 5
    TAGS = 6
    CONTENT_TAGS = 7
    META_TAGS = 8
    DATE_PUBLISHED = 14
    SOURCE = 21


class OpenStatus(enum.IntEnum):
    NOT_FOUND = 0
    SUCCESS = 1
    CORRUPTED = 2
