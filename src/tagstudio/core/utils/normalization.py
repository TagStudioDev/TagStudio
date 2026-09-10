# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import unicodedata
from pathlib import Path


def norm_path(path: Path | str, case_sensitive: bool) -> Path:
    """Return `path` normalized to Unicode Normalization Form D (NFD)."""
    if isinstance(path, str):
        path = Path(path)
    normalized = unicodedata.normalize("NFD", path.as_posix())
    if not case_sensitive:
        normalized = normalized.casefold()
    return Path(normalized)
