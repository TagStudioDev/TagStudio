# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import shutil
from pathlib import Path

import pytest

from tagstudio.core.constants import IGNORE_NAME, TS_FOLDER_NAME
from tagstudio.core.library.alchemy.constants import (
    SQL_FILENAME,
)
from tagstudio.core.library.alchemy.library import Library

CWD = Path(__file__)
FIXTURES = "fixtures"
EMPTY_LIBRARIES = "empty_libraries"


@pytest.mark.parametrize(
    "path",
    [
        str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_6")),
        str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_7")),
        str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_8")),
        str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_9")),
        str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_100")),
        str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_101")),
        # str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_102")),
        str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_103")),
        str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_200")),
        str(Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_201")),
    ],
)
def test_library_migrations(path: str):
    library = Library()

    # Copy libraries to temp dir so modifications don't show up in version control
    original_path = Path(path)
    temp_path = Path(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_TEMP")
    temp_path.mkdir(exist_ok=True)
    temp_path_ts = temp_path / TS_FOLDER_NAME
    temp_path_ts.mkdir(exist_ok=True)
    shutil.copy(
        original_path / TS_FOLDER_NAME / SQL_FILENAME,
        temp_path / TS_FOLDER_NAME / SQL_FILENAME,
    )

    try:
        status = library.open_library(library_dir=temp_path)
        library.close()
        assert status.success
    except Exception as e:
        library.close()
        raise (e)
    finally:
        shutil.rmtree(temp_path)


def test_migration_with_existing_field_template_tables(tmp_path: Path):
    """DB_VERSION 104 library that already has the (empty) field template tables.

    v9.6.0-9.6.2 created these empty tables before migrating, so backup library files
    or libraries that failed mid-migration may already have them.

    This tests for a specific scenario where a backup library file from a
    v9.5.6 (DB102) -> v9.6.2 (DB300) migration is opened in a newer version.
    Historically this would cause breakage in v9.6.3 (see issue #1500).
    """
    fixture = CWD.parents[2] / FIXTURES / "issue-1500" / TS_FOLDER_NAME / SQL_FILENAME
    (tmp_path / TS_FOLDER_NAME).mkdir()
    shutil.copy(fixture, tmp_path / TS_FOLDER_NAME / SQL_FILENAME)

    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
        expected = ["Title", "Author", "Artist", "URL", "Description", "Notes", "Comments", "Date"]
        assert [t.name for t in library.field_templates] == expected

        assert library.entries_count == 2
        entry = library.get_entry_full(entry_id=2)
        assert entry
        assert {f.name: f.value for f in entry.text_fields} == {
            "Title": "Mario",
            "Description": "This is a cat.",
        }
        assert {f.name: f.value for f in entry.datetime_fields} == {
            "Date": None,
        }
    finally:
        library.close()


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("# Comment\n*\n!*.png\n*\n", "# Comment\n*\n!*/\n!*.png\n*\n"),
        ("*\n!*/\n!*.png\n", "*\n!*/\n!*.png\n"),
        ("*.jpg\n", "*.jpg\n"),
    ],
)
def test_migration_to_500_reincludes_ts_ignore_folders(tmp_path: Path, before: str, after: str):
    """A .ts_ignore that ignores everything with "*" must get "!*/" after the first occurrence

    If there's more than one occurrence... *why...*
    """
    fixture = CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_202" / TS_FOLDER_NAME
    (tmp_path / TS_FOLDER_NAME).mkdir()
    shutil.copy(fixture / SQL_FILENAME, tmp_path / TS_FOLDER_NAME / SQL_FILENAME)
    ts_ignore = tmp_path / TS_FOLDER_NAME / IGNORE_NAME
    ts_ignore.write_text(before)

    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
    finally:
        library.close()
    assert ts_ignore.read_text() == after
