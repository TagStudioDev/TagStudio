# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

def strip_punctuation(text: str) -> str:
    """Returns a given string stripped of all punctuation characters."""
    punctuation = '{}[]()\'"`‘’“”-_ 　'
    result = text

    for p in punctuation:
        result = result.replace(p, '')

    return result

