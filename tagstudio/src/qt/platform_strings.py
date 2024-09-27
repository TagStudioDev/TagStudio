# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""A collection of platform-dependant strings."""

import platform


class PlatformStrings:
    open_file_str: str = "Open in file explorer"

    if platform.system() == "Windows":
        open_file_str = "Open in Explorer"
    elif platform.system() == "Darwin":
        open_file_str = "Reveal in Finder"
