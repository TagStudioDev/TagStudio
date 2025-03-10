# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


def strip_punctuation(string: str) -> str:
    """Returns a given string stripped of all punctuation characters."""
    return (
        string.replace("(", "")
        .replace(")", "")
        .replace("[", "")
        .replace("]", "")
        .replace("{", "")
        .replace("}", "")
        .replace("'", "")
        .replace("`", "")
        .replace("’", "")
        .replace("‘", "")
        .replace('"', "")
        .replace("“", "")
        .replace("”", "")
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("　", "")
    )
