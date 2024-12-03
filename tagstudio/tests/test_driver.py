from os import makedirs
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QSettings
from src.core.constants import TS_FOLDER_NAME
from src.core.driver import DriverMixin
from src.core.enums import SettingItems
from src.core.library.alchemy.library import LibraryStatus


class TestDriver(DriverMixin):
    def __init__(self, settings):
        self.settings = settings


def test_evaluate_path_empty():
    # Given
    settings = QSettings()
    driver = TestDriver(settings)

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == LibraryStatus(success=True)


def test_evaluate_path_missing():
    # Given
    settings = QSettings()
    driver = TestDriver(settings)

    # When
    result = driver.evaluate_path("/0/4/5/1/")

    # Then
    assert result == LibraryStatus(success=False, message="Path does not exist.")


def test_evaluate_path_last_lib_not_exists():
    # Given
    settings = QSettings()
    settings.setValue(SettingItems.LAST_LIBRARY, "/0/4/5/1/")
    driver = TestDriver(settings)

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == LibraryStatus(success=True, library_path=None, message=None)


def test_evaluate_path_last_lib_present():
    # Given
    with TemporaryDirectory() as tmpdir:
        settings_file = tmpdir + "/test_settings.ini"
        settings = QSettings(settings_file, QSettings.Format.IniFormat)
        settings.setValue(SettingItems.LAST_LIBRARY, tmpdir)
        settings.sync()

        makedirs(Path(tmpdir) / TS_FOLDER_NAME)
        driver = TestDriver(settings)

        # When
        result = driver.evaluate_path(None)

        # Then
        assert result == LibraryStatus(success=True, library_path=Path(tmpdir))
