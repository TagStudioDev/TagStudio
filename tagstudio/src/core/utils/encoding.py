# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from chardet.universaldetector import UniversalDetector
from pathlib import Path


def detect_char_encoding(filepath: Path) -> str | None:
    """
    Attempts to detect the character encoding of a text file.

    Args:
    filepath (Path): The path of the text file to analyze.

    Returns:
    str | None: The detected character encoding, if any.
    """

    detector = UniversalDetector()
    with open(filepath, "rb") as text_file:
        for line in text_file.readlines():
            detector.feed(line)
            if detector.done:
                break
        detector.close()
    return detector.result["encoding"]
