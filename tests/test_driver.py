from os import makedirs
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QSettings

from tagstudio.core.constants import TS_FOLDER_NAME
from tagstudio.core.driver import DriverMixin
from tagstudio.core.enums import SettingItems
from tagstudio.core.global_settings import GlobalSettings
from tagstudio.core.library.alchemy.library import LibraryStatus


class TestDriver(DriverMixin):
    def __init__(self, settings: GlobalSettings, cache: QSettings):
        self.settings = settings
        self.cached_values = cache


def test_evaluate_path_empty():
    # Given
    driver = TestDriver(GlobalSettings(), QSettings())

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == LibraryStatus(success=True)


def test_evaluate_path_missing():
    # Given
    driver = TestDriver(GlobalSettings(), QSettings())

    # When
    result = driver.evaluate_path("/0/4/5/1/")

    # Then
    assert result == LibraryStatus(success=False, message="Path does not exist.")


def test_evaluate_path_last_lib_not_exists():
    # Given
    cache = QSettings()
    cache.setValue(SettingItems.LAST_LIBRARY, "/0/4/5/1/")
    driver = TestDriver(GlobalSettings(), cache)

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == LibraryStatus(success=True, library_path=None, message=None)


def test_evaluate_path_last_lib_present():
    # Given
    with TemporaryDirectory() as tmpdir:
        cache_file = tmpdir + "/test_settings.ini"
        cache = QSettings(cache_file, QSettings.Format.IniFormat)
        cache.setValue(SettingItems.LAST_LIBRARY, tmpdir)
        cache.sync()

        settings = GlobalSettings()
        settings.open_last_loaded_on_startup = True

        makedirs(Path(tmpdir) / TS_FOLDER_NAME)
        driver = TestDriver(settings, cache)

        # When
        result = driver.evaluate_path(None)

        # Then
        assert result == LibraryStatus(success=True, library_path=Path(tmpdir))
