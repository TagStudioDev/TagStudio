# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


def strip_web_protocol(string: str) -> str:
    r"""Strips a leading web protocol (ex. \"https://\") as well as \"www.\" from a string."""
    prefixes = ["https://", "http://", "www.", "www2."]
    for prefix in prefixes:
        string = string.removeprefix(prefix)
    return string
