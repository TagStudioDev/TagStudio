from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.settings.tssettings import TSSettings


def test_read_settings():
    with TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / "example_settings.toml"
        with open(settings_path, "a") as settings_file:
            settings_file.write("""
    language = "en"
    open_last_loaded_on_startup = false
    show_filenames_in_grid = true
    autoplay = false
    filename = ""
    """)

        settings = TSSettings.read_settings(settings_path)
        assert settings.language == "en"
        assert not settings.open_last_loaded_on_startup
        assert settings.show_filenames_in_grid
        assert not settings.autoplay
