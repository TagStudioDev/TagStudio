# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

import os
import platform
from pathlib import Path


def _resolve(path_or_stat: Path | os.stat_result) -> os.stat_result:
    if isinstance(path_or_stat, os.stat_result):
        return path_or_stat
    return path_or_stat.stat()


def get_date_modified(path_or_stat: Path | os.stat_result) -> float:
    return _resolve(path_or_stat).st_mtime


def get_date_created(path_or_stat: Path | os.stat_result) -> float:
    stat = _resolve(path_or_stat)
    if platform.system() in {"Windows", "Darwin"}:
        return stat.st_birthtime
    else:
        return stat.st_ctime


def get_file_size(path_or_stat: Path | os.stat_result) -> int:
    return _resolve(path_or_stat).st_size
