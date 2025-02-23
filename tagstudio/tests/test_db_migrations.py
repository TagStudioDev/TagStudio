# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.core.library.alchemy.library import Library

CWD = Path(__file__)
FIXTURES = "fixtures"
EMPTY_LIBRARIES = "empty_libraries"


@pytest.mark.parametrize(
    "path",
    [
        str(Path(CWD / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_6")),
        str(Path(CWD / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_7")),
        str(Path(CWD / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_8")),
    ],
)
def test_library_migrations(library: "Library", path: str):
    status = library.open_library(library_dir=Path(path), storage_path=None)
    assert status.success
