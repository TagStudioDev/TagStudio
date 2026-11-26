# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

from tagstudio.qt.app_settings import (
    AppSettings,
    ShowFilepathOption,
    ThemeOption,
    migrate_legacy_settings,
)


def test_saved_settings_load_saved_values(tmp_path: Path):
    path = tmp_path / "app_settings.toml"
    settings = AppSettings.load(path)
    settings.theme = ThemeOption.LIGHT
    settings.show_filepath = ShowFilepathOption.SHOW_FILENAMES_ONLY
    settings.save()

    loaded_settings = AppSettings.load(path)

    assert loaded_settings.theme == ThemeOption.LIGHT
    assert loaded_settings.show_filepath == ShowFilepathOption.SHOW_FILENAMES_ONLY


def test_page_size_snaps_to_nearest_preset():
    assert AppSettings(page_size=300).page_size == 250


def test_migrate_legacy_settings_moves_file(tmp_path: Path):
    legacy_path = tmp_path / "settings.toml"
    legacy_path.write_text('language = "de"\n', encoding="utf-8")
    path = tmp_path / "TagStudio" / "app_settings.toml"

    migrate_legacy_settings(legacy_path, path)

    assert AppSettings.load(path).language == "de"


def test_migrate_legacy_settings_keeps_existing_settings(tmp_path: Path):
    legacy_path = tmp_path / "settings.toml"
    legacy_path.write_text('language = "de"\n', encoding="utf-8")
    path = tmp_path / "app_settings.toml"
    path.write_text('language = "en"\n', encoding="utf-8")

    migrate_legacy_settings(legacy_path, path)

    assert AppSettings.load(path).language == "en"


def test_migrate_legacy_settings_keeps_legacy_file_if_move_fails(tmp_path: Path):
    legacy_path = tmp_path / "settings.toml"
    legacy_path.write_text('language = "de"\n', encoding="utf-8")
    blocking_file = tmp_path / "TagStudio"
    blocking_file.write_text("", encoding="utf-8")

    migrate_legacy_settings(legacy_path, blocking_file / "app_settings.toml")

    assert legacy_path.exists()
