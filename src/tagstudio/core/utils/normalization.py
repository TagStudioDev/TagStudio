# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import unicodedata
from pathlib import Path


def norm_path(path: Path | str, case_sensitive: bool) -> Path:
    """Return `path` normalized to Unicode Normalization Form D (NFD)."""
    if isinstance(path, str):
        path = Path(path)
    posix = path.as_posix()
    # NOTE: ASCII paths will be unaffected by all unicode normalization and can be skipped.
    # See: https://unicode.org/reports/tr15/
    normalized = posix if posix.isascii() else unicodedata.normalize("NFD", posix)
    if not case_sensitive:
        normalized = normalized.casefold()
    return Path(normalized)
