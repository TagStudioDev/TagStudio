# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


def strip_web_protocol(string: str) -> str:
    """Strips a leading web protocol (ex. \"https://\") as well as \"www.\" from a string."""
    new_str = string
    new_str = new_str.removeprefix("https://")
    new_str = new_str.removeprefix("http://")
    new_str = new_str.removeprefix("www.")
    new_str = new_str.removeprefix("www2.")
    return new_str
