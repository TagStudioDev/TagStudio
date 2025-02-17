# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import enum
from typing import Any
from uuid import uuid4


class SettingItems(str, enum.Enum):
    """List of setting item names."""

    START_LOAD_LAST = "start_load_last"
    LAST_LIBRARY = "last_library"
    LIBS_LIST = "libs_list"
    WINDOW_SHOW_LIBS = "window_show_libs"
    SHOW_FILENAMES = "show_filenames"
    AUTOPLAY = "autoplay_videos"
    THUMB_CACHE_SIZE_LIMIT = "thumb_cache_size_limit"
    LANGUAGE = "language"


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
    EXTENSION_LIST: list[str] = [".json", ".xmp", ".aae"]
    PAGE_SIZE: int = 500
    DB_VERSION: int = 8
