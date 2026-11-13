# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

from chardet.universaldetector import UniversalDetector


def detect_char_encoding(filepath: Path) -> str | None:
    """Attempts to detect the character encoding of a text file.

    Args:
    filepath (Path): The path of the text file to analyze.

    Returns:
    str | None: The detected character encoding, if any.
    """
    with open(filepath, "rb") as text_file:
        data = text_file.read()

    # chardet gives UTF-8 a low confidence when a file has only a few multi-byte
    # characters (such as a couple of emoji), and then picks a single-byte
    # encoding like Windows-1252 instead. Bytes that decode as UTF-8 are UTF-8.
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass

    detector = UniversalDetector()
    for line in data.splitlines(keepends=True):
        detector.feed(line)
        if detector.done:
            break
    detector.close()
    return detector.result["encoding"]
