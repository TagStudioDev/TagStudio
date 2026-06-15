# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

from tagstudio.qt.global_settings import GlobalSettings, Theme


def test_read_settings(library_dir: Path):
    settings_path = library_dir / "settings.toml"
    with open(settings_path, "w") as settings_file:
        settings_file.write("""
            language = "de"
            open_last_loaded_on_startup = true
            autoplay = true
            show_filenames_in_grid = true
            page_size = 1337
            show_filepath = 0
            dark_mode = 2
            date_format = "%x"
            hour_format = true
            zero_padding = true
        """)

    settings = GlobalSettings.read_settings(settings_path)
    assert settings.language == "de"
    assert settings.open_last_loaded_on_startup
    assert settings.autoplay
    assert settings.show_filenames_in_grid
    assert settings.page_size == 1337
    assert settings.show_filepath == 0
    assert settings.theme == Theme.SYSTEM
    assert settings.date_format == "%x"
    assert settings.hour_format
    assert settings.zero_padding


def test_read_settings_legacy_locale_encoding(library_dir: Path, monkeypatch):
    settings_path = library_dir / "settings.toml"
    settings_path.write_bytes(
        b'language = "ja"\ndate_format = "' + "写真".encode("cp932") + b'"\n'
    )
    monkeypatch.setattr("tagstudio.qt.global_settings.detect_char_encoding", lambda _: None)
    monkeypatch.setattr("tagstudio.qt.global_settings.locale.getencoding", lambda: "cp932")

    settings = GlobalSettings.read_settings(settings_path)
    settings.save()

    assert settings.date_format == "写真"
    assert settings_path.read_bytes().decode("utf-8")
