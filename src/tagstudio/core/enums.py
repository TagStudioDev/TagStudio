# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import enum


class AppCacheItems(enum.StrEnum):
    """List of setting item names."""

    LAST_LIBRARY = "last_library"
    LIBS_LIST = "libs_list"
    DISMISSED_UPDATE = "dismissed_update"


class ShowFilepathOption(enum.IntEnum):
    """Values representing the options for the "show_filenames" setting."""

    SHOW_FULL_PATHS = 0
    SHOW_RELATIVE_PATHS = 1
    SHOW_FILENAMES_ONLY = 2
    DEFAULT = SHOW_RELATIVE_PATHS


class TagClickActionOption(enum.IntEnum):
    """Values representing the options for the "tag_click_action" setting."""

    OPEN_EDIT = 0
    SET_SEARCH = 1
    ADD_TO_SEARCH = 2
    DEFAULT = OPEN_EDIT


class Theme(enum.StrEnum):
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


class MacroID(enum.StrEnum):
    AUTOFILL = "autofill"
    SIDECAR = "sidecar"
    BUILD_URL = "build_url"
    MATCH = "match"
    CLEAN_URL = "clean_url"
