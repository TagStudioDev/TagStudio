# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import pathlib

from src.core.enums import LibraryPrefs
from src.qt.widgets.migration_modal import JsonMigrationModal  # type: ignore

CWD = pathlib.Path(__file__)


def test_json_migration():
    modal = JsonMigrationModal(CWD.parent / "fixtures" / "json_library")
    modal.migrate()

    # Entries ==================================================================
    # Count
    assert len(modal.json_lib.entries) == modal.sql_lib.entries_count

    # Tags =====================================================================
    # Count
    assert len(modal.json_lib.tags) == len(modal.sql_lib.tags)

    # Extension Filter List ====================================================
    # Count
    assert len(modal.json_lib.ext_list) == len(modal.sql_lib.prefs(LibraryPrefs.EXTENSION_LIST))
    # List Type
    assert modal.json_lib.is_exclude_list == modal.sql_lib.prefs(LibraryPrefs.IS_EXCLUDE_LIST)
    # No Leading Dot
    for ext in modal.sql_lib.prefs(LibraryPrefs.EXTENSION_LIST):
        assert ext[0] != "."
