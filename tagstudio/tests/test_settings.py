import pathlib

from src.core.settings.tssettings import TSSettings

CWD = pathlib.Path(__file__)


def test_read_settings():
    settings = TSSettings.read_settings(CWD.parent / "example_settings.toml")
    assert settings.language == "en"
    assert not settings.open_last_loaded_on_startup
    assert settings.show_filenames_in_grid
    assert not settings.autoplay
