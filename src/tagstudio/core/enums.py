# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import enum
from typing import Any
from uuid import uuid4


class SettingItems(str, enum.Enum):
    """List of setting item names."""

    LAST_LIBRARY = "last_library"
    LIBS_LIST = "libs_list"
    THUMB_CACHE_SIZE_LIMIT = "thumb_cache_size_limit"


class ShowFilepathOption(int, enum.Enum):
    """Values representing the options for the "show_filenames" setting."""

    SHOW_FULL_PATHS = 0
    SHOW_RELATIVE_PATHS = 1
    SHOW_FILENAMES_ONLY = 2
    DEFAULT = SHOW_RELATIVE_PATHS


class TagClickActionOption(int, enum.Enum):
    """Values representing the options for the "tag_click_action" setting."""

    OPEN_EDIT = 0
    SET_SEARCH = 1
    ADD_TO_SEARCH = 2
    DEFAULT = OPEN_EDIT


class Theme(str, enum.Enum):
    COLOR_BG_DARK = "#65000000"
    COLOR_BG_LIGHT = "#22000000"
    COLOR_DARK_LABEL = "#DD000000"
    COLOR_BG = "#65000000"

    COLOR_HOVER = "#65444444"
    COLOR_PRESSED = "#65777777"
    COLOR_DISABLED_BG = "#30000000"
    COLOR_FORBIDDEN = "#65F39CAA"
    COLOR_FORBIDDEN_BG = "#65440D12"


class OpenStatus(enum.IntEnum):
    NOT_FOUND = 0
    SUCCESS = 1
    CORRUPTED = 2


class MacroID(enum.Enum):
    AUTOFILL = "autofill"
    SIDECAR = "sidecar"
    BUILD_URL = "build_url"
    MATCH = "match"
    CLEAN_URL = "clean_url"


class DefaultEnum(enum.Enum):
    """Allow saving multiple identical values in property called .default."""

    default: Any

    def __new__(cls, value):
        # Create the enum instance
        obj = object.__new__(cls)
        # make value random
        obj._value_ = uuid4()
        # assign the actual value into .default property
        obj.default = value
        return obj

    @property
    def value(self):
        raise AttributeError("access the value via .default property instead")


class LibraryPrefs(DefaultEnum):
    """Library preferences with default value accessible via .default property."""

    IS_EXCLUDE_LIST = True
    EXTENSION_LIST = [".json", ".xmp", ".aae"]
    DB_VERSION = 9
