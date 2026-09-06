# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

import platform
from pathlib import Path


def get_date_modified(path: Path) -> float:
    return path.stat().st_mtime


def get_date_created(path: Path) -> float:
    if platform.system() in {"Windows", "Darwin"}:
        return path.stat().st_birthtime
    else:
        return path.stat().st_ctime
