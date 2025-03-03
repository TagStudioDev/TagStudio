# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import pathlib
from time import time

from src.core.enums import LibraryPrefs
from src.qt.widgets.migration_modal import JsonMigrationModal

CWD = pathlib.Path(__file__)


def test_json_migration():
    modal = JsonMigrationModal(CWD.parent / "fixtures" / "json_library")
    modal.migrate(skip_ui=True)

    start = time()
    while not modal.done and (time() - start < 60):
        pass

    # Entries ==================================================================
    # Count
    assert len(modal.json_lib.entries) == modal.sql_lib.entries_count
    # Path Parity
    assert modal.check_path_parity()
    # Field Parity
    assert modal.check_field_parity()

    # Tags =====================================================================
    # Count
    assert len(modal.json_lib.tags) == len(modal.sql_lib.tags)
    # Name Parity
    assert modal.check_name_parity()
    # Shorthand Parity
    assert modal.check_shorthand_parity()
    # Subtag/Parent Tag Parity
    assert modal.check_subtag_parity()
    # Alias Parity
    assert modal.check_alias_parity()
    # Color Parity
    assert modal.check_color_parity()

    # Extension Filter List ====================================================
    # Count
    assert len(modal.json_lib.ext_list) == len(modal.sql_lib.prefs(LibraryPrefs.EXTENSION_LIST))
    # List Type
    assert modal.check_ext_type()
    # No Leading Dot
    for ext in modal.sql_lib.prefs(LibraryPrefs.EXTENSION_LIST):
        assert ext[0] != "."
