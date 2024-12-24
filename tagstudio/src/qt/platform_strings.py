# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""A collection of platform-dependant strings."""

import platform

from src.qt.translations import Translations


class PlatformStrings:
    open_file_str: str = Translations["file.open_location.generic"]

    if platform.system() == "Windows":
        open_file_str = Translations["file.open_location.windows"]
    elif platform.system() == "Darwin":
        open_file_str = Translations["file.open_location.mac"]
