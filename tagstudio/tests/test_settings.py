import pathlib

from src.core.settings.tssettings import TSSettings

CWD = pathlib.Path(__file__)


def test_read_settings():
    settings = TSSettings.read_settings(CWD.parent / "example_settings.toml")
    assert settings.dark_mode
    assert settings.language == "es-MX"
