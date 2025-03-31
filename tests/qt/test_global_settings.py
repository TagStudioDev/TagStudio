from pathlib import Path
from tempfile import TemporaryDirectory

from tagstudio.core.global_settings import GlobalSettings, Theme


def test_read_settings():
    with TemporaryDirectory() as tmp_dir:
        settings_path = Path(tmp_dir) / "settings.toml"
        with open(settings_path, "a") as settings_file:
            settings_file.write("""
                language = "de"
                open_last_loaded_on_startup = true
                autoplay = true
                show_filenames_in_grid = true
                page_size = 1337
                show_filepath = 0
                dark_mode = 2
            """)

        settings = GlobalSettings.read_settings(settings_path)
        assert settings.language == "de"
        assert settings.open_last_loaded_on_startup
        assert settings.autoplay
        assert settings.show_filenames_in_grid
        assert settings.page_size == 1337
        assert settings.show_filepath == 0
        assert settings.theme == Theme.SYSTEM
