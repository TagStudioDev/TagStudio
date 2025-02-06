# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""A collection of platform-dependant strings."""

import platform

from src.qt.translations import Translations


def open_file_str() -> str:
    if platform.system() == "Windows":
        return Translations["file.open_location.windows"]
    elif platform.system() == "Darwin":
        return Translations["file.open_location.mac"]
    else:
        return Translations["file.open_location.generic"]


def trash_term() -> str:
    if platform.system() == "Windows":
        return Translations["trash.name.windows"]
    else:
        return Translations["trash.name.generic"]
