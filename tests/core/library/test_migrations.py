# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from tagstudio.core.constants import IGNORE_NAME, TS_FOLDER_NAME
from tagstudio.core.library.alchemy.constants import (
    SQL_FILENAME,
)
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry

CWD = Path(__file__)
FIXTURES = "fixtures"
EMPTY_LIBRARIES = "empty_libraries"
ENTRY_INDEXES = {"idx_entries_id", "idx_entries_suffix"}


def entries_index_names(sql_path: Path) -> set[str]:
    with closing(sqlite3.connect(sql_path)) as connection:
        return {row[1] for row in connection.execute("PRAGMA index_list(entries)")}


def pragma_value(sql_path: Path, pragma: str) -> object:
    with closing(sqlite3.connect(sql_path)) as connection:
        return connection.execute(f"PRAGMA {pragma}").fetchone()[0]


def copy_fixture_library(fixture_dir: Path, library_dir: Path) -> None:
    (library_dir / TS_FOLDER_NAME).mkdir()
    shutil.copy(
        fixture_dir / TS_FOLDER_NAME / SQL_FILENAME, library_dir / TS_FOLDER_NAME / SQL_FILENAME
    )


def entry_rows(sql_path: Path) -> list[tuple[object, ...]]:
    with closing(sqlite3.connect(sql_path)) as connection:
        return connection.execute(
            "SELECT id, path, filename, suffix, date_created, date_modified, file_size, date_added "
            "FROM entries ORDER BY id"
        ).fetchall()


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
    copy_fixture_library(CWD.parents[2] / FIXTURES / "issue-1500", tmp_path)

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


def test_migration_to_501_adds_entry_indexes(tmp_path: Path):
    copy_fixture_library(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_202", tmp_path)

    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
    finally:
        library.close()
    assert entries_index_names(tmp_path / TS_FOLDER_NAME / SQL_FILENAME) >= ENTRY_INDEXES


def test_new_library_has_entry_indexes(tmp_path: Path):
    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
    finally:
        library.close()
    assert entries_index_names(tmp_path / TS_FOLDER_NAME / SQL_FILENAME) >= ENTRY_INDEXES


def test_migration_to_501_sets_32_kb_page_size(tmp_path: Path):
    copy_fixture_library(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_202", tmp_path)

    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
    finally:
        library.close()
    assert pragma_value(tmp_path / TS_FOLDER_NAME / SQL_FILENAME, "page_size") == 32768


def test_migration_to_501_keeps_wal_mode(tmp_path: Path):
    # NOTE: The 501 migration also has to set the new page size before WAL mode is set, so that
    # could be a sneaky issue that pops up if WAL mode is set in the wrong order.
    copy_fixture_library(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_202", tmp_path)

    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
    finally:
        library.close()
    assert pragma_value(tmp_path / TS_FOLDER_NAME / SQL_FILENAME, "journal_mode") == "wal"


def test_new_library_has_32_kb_page_size(tmp_path: Path):
    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
    finally:
        library.close()
    assert pragma_value(tmp_path / TS_FOLDER_NAME / SQL_FILENAME, "page_size") == 32768


def test_migration_to_501_keeps_entries(tmp_path: Path):
    copy_fixture_library(CWD.parents[2] / FIXTURES / "search_library", tmp_path)
    entries_before = entry_rows(tmp_path / TS_FOLDER_NAME / SQL_FILENAME)

    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
    finally:
        library.close()
    assert entry_rows(tmp_path / TS_FOLDER_NAME / SQL_FILENAME) == entries_before


def test_migration_to_501_prevents_entry_id_reuse(tmp_path: Path):
    copy_fixture_library(CWD.parents[2] / FIXTURES / "search_library", tmp_path)

    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
        removed_id = library.add_entries([Entry(path=Path("removed.txt"), fields=[])])[0]
        library.remove_entries([removed_id])
        assert library.add_entries([Entry(path=Path("new.txt"), fields=[])])[0] != removed_id
    finally:
        library.close()


def test_new_library_prevents_entry_id_reuse(tmp_path: Path):
    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
        removed_id = library.add_entries([Entry(path=Path("removed.txt"), fields=[])])[0]
        library.remove_entries([removed_id])
        assert library.add_entries([Entry(path=Path("new.txt"), fields=[])])[0] != removed_id
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
    copy_fixture_library(CWD.parents[2] / FIXTURES / EMPTY_LIBRARIES / "DB_VERSION_202", tmp_path)
    ts_ignore = tmp_path / TS_FOLDER_NAME / IGNORE_NAME
    ts_ignore.write_text(before)

    library = Library()
    try:
        assert library.open_library(library_dir=tmp_path).success
    finally:
        library.close()
    assert ts_ignore.read_text() == after
