# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import shutil
from pathlib import Path

import pytest
from src.core.constants import TS_FOLDER_NAME
from src.core.library.alchemy.library import Library

CWD = Path(__file__)
FIXTURES = "fixtures"
EMPTY_LIBRARIES = "empty_libraries"


@pytest.mark.parametrize(
    "path",
    [
        str(Path(CWD.parent / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_6")),
        str(Path(CWD.parent / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_7")),
        str(Path(CWD.parent / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_8")),
    ],
)
def test_library_migrations(path: str):
    library = Library()

    # Copy libraries to temp dir so modifications don't show up in version control
    original_path = Path(path)
    temp_path = Path(CWD.parent / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_TEMP")
    temp_path.mkdir(exist_ok=True)
    temp_path_ts = temp_path / TS_FOLDER_NAME
    temp_path_ts.mkdir(exist_ok=True)
    shutil.copy(
        original_path / TS_FOLDER_NAME / Library.SQL_FILENAME,
        temp_path / TS_FOLDER_NAME / Library.SQL_FILENAME,
    )

    try:
        status = library.open_library(library_dir=temp_path)
        library.close()
        shutil.rmtree(temp_path)
        assert status.success
    except Exception as e:
        library.close()
        shutil.rmtree(temp_path)
        raise (e)
