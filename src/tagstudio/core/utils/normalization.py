# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import unicodedata
from pathlib import Path
from typing import Literal

from tagstudio.core.utils.filesystem import is_fs_case_sensitive


def norm_path(
    path: Path | str, case_sensitive: bool, form: Literal["NFC", "NFKC", "NFD", "NFKD"] = "NFD"
) -> Path:
    """Return a Unicode-normalized Path. Uses Unicode Normalization Form D (NFD) by default.

    NOTE: NFD is the intended form for all TagStudio storage and comparisons. Some paths need other
    forms when referencing live files on disk.
    """
    if isinstance(path, str):
        path = Path(path)
    return Path(norm_str(path.as_posix(), case_sensitive=case_sensitive, form=form))


def norm_str(
    string: str, case_sensitive: bool, form: Literal["NFC", "NFKC", "NFD", "NFKD"] = "NFD"
) -> str:
    """Return a Unicode-normalized string. Uses Unicode Normalization Form D (NFD) by default."""
    # NOTE: ASCII strings will be unaffected by all unicode normalization and can be skipped.
    # See: https://unicode.org/reports/tr15/
    normalized = string if string.isascii() else unicodedata.normalize(form, string)
    if not case_sensitive:
        normalized = normalized.casefold()
    return normalized


def path_on_disk(path: Path) -> Path:
    """Un-normalize a path stored in a TagStudio library to match the form located on disk.

    Returns the original path if path does not exist on disk.
    """
    if path.exists():
        return path

    # NOTE: Case sensitivity is True here since it's irrelevant to callers.
    nfc_path = norm_path(path, case_sensitive=True, form="NFC")
    if nfc_path.exists():
        return nfc_path

    return path


def exists(path: Path) -> bool:
    """Wrapper for `pathlib.Path.exists()` that's Unicode Normalization Form agnostic."""
    # NOTE: Initial path will always be in NFD
    return path.exists() or norm_path(path, is_fs_case_sensitive(), "NFC").exists()


def is_file(path: Path) -> bool:
    """Wrapper for `pathlib.Path.is_file()` that's Unicode Normalization Form agnostic."""
    # NOTE: Initial path will always be in NFD
    return path.is_file() or norm_path(path, is_fs_case_sensitive(), "NFC").is_file()
