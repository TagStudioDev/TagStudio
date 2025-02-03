# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


def escape_text(text: str):
    """Escapes characters that are problematic in Qt widgets."""
    return text.replace("&", "&&")
