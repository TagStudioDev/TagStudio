# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import re

_space_regex = re.compile("\\s+")


def replace_whitespace(string: str) -> str:
    """Returns a given string replacing all runs of whitespace characters with underscore _."""
    return re.sub(_space_regex, "_", string)
