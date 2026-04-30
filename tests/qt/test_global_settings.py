# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from pathlib import Path

from tagstudio.core.constants import (
    DEFAULT_COMIC_INFO_MAX_MB,
    DEFAULT_DUPE_RESULTS_MAX_MB,
    DEFAULT_MDP_HEADER_MAX_MB,
    DEFAULT_PDN_HEADER_MAX_MB,
)
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


def test_security_cap_defaults():
    """Default cap values match the canonical constants in core.constants."""
    settings = GlobalSettings()
    assert settings.dupe_results_max_mb == DEFAULT_DUPE_RESULTS_MAX_MB
    assert settings.comic_info_max_mb == DEFAULT_COMIC_INFO_MAX_MB
    assert settings.mdp_header_max_mb == DEFAULT_MDP_HEADER_MAX_MB
    assert settings.pdn_header_max_mb == DEFAULT_PDN_HEADER_MAX_MB


def test_security_caps_round_trip(tmp_path: Path):
    """The four cap fields persist through save -> read_settings."""
    settings_path = tmp_path / "settings.toml"
    settings = GlobalSettings(
        loaded_from=settings_path,
        dupe_results_max_mb=256,
        comic_info_max_mb=4,
        mdp_header_max_mb=8,
        pdn_header_max_mb=32,
    )
    settings.save()

    reloaded = GlobalSettings.read_settings(settings_path)
    assert reloaded.dupe_results_max_mb == 256
    assert reloaded.comic_info_max_mb == 4
    assert reloaded.mdp_header_max_mb == 8
    assert reloaded.pdn_header_max_mb == 32
