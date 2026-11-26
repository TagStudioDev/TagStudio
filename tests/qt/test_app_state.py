# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

from PySide6.QtCore import QSettings

from tagstudio.qt.app_state import AppState, migrate_legacy_cache


def write_legacy_cache(path: Path) -> None:
    cache = QSettings(str(path), QSettings.Format.IniFormat)
    cache.setValue("last_library", "/libraries/b")
    cache.setValue("libs_list/1700000000.0", "/libraries/a")
    cache.setValue("libs_list/1700000001.0", "/libraries/b")
    cache.setValue("dismissed_update", "9.9.9")
    cache.setValue("last_version_opened", "9.5.0")
    cache.sync()


def test_add_recent_library_moves_listed_library_to_front():
    state = AppState(recent_libraries=[Path("/a"), Path("/b"), Path("/c")])

    state.add_recent_library(Path("/c"))

    assert state.recent_libraries == [Path("/c"), Path("/a"), Path("/b")]


def test_migrate_legacy_cache_converts_values(tmp_path: Path):
    legacy_path = tmp_path / "TagStudio.ini"
    write_legacy_cache(legacy_path)
    path = tmp_path / "app_state.json"
    expected_state = AppState(
        last_library=Path("/libraries/b"),
        recent_libraries=[Path("/libraries/b"), Path("/libraries/a")],
        dismissed_update="9.9.9",
        last_version_opened="9.5.0",
    )

    migrate_legacy_cache(legacy_path, path)

    assert AppState.load(path).model_dump() == expected_state.model_dump()


def test_migrate_legacy_cache_deletes_legacy_file(tmp_path: Path):
    legacy_path = tmp_path / "TagStudio.ini"
    write_legacy_cache(legacy_path)

    migrate_legacy_cache(legacy_path, tmp_path / "app_state.json")

    assert not legacy_path.exists()


def test_migrate_legacy_cache_keeps_legacy_file_if_save_fails(tmp_path: Path):
    legacy_path = tmp_path / "TagStudio.ini"
    write_legacy_cache(legacy_path)
    blocking_file = tmp_path / "TagStudio"
    blocking_file.write_text("", encoding="utf-8")

    migrate_legacy_cache(legacy_path, blocking_file / "app_state.json")

    assert legacy_path.exists()
