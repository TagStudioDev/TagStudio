# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path
from src.core.constants import ENCODINGS


def get_text_encoding(filepath: Path) -> str:
    """
    Attempts to determine the encoding of a text file.

    Args:
    file (TextIOWrapper): The text file to analyze.

    Returns:
    str: The assumed encoding. Defaults to utf-8.
    """

    for encoding in ENCODINGS:
        with open(filepath, "r", encoding=encoding) as text_file:
            try:
                text_file.read(16)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                pass

    return "utf-8"
