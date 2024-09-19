from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QSettings
from src.core.driver import DriverMixin
from src.core.enums import SettingItems
from src.core.library.alchemy.library import LibraryStatus


class DriverTest(DriverMixin):
    def __init__(self, settings):
        self.settings = settings


def test_evaluate_path_empty():
    # Given
    settings = QSettings()
    driver = DriverTest(settings)

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == LibraryStatus(success=True)


def test_evaluate_path_missing():
    # Given
    settings = QSettings()
    driver = DriverTest(settings)

    # When
    result = driver.evaluate_path("/0/4/5/1/")

    # Then
    assert result == LibraryStatus(success=False, message="Path does not exist.")


def test_evaluate_path_last_lib_not_exists():
    # Given
    settings = QSettings()
    settings.setValue(SettingItems.LAST_LIBRARY, "/0/4/5/1/")
    driver = DriverTest(settings)

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == LibraryStatus(success=True, storage_path=None, message=None)


def test_evaluate_path_last_lib_present():
    # Given
    settings = QSettings()
    with TemporaryDirectory() as tmpdir:
        settings.setValue(SettingItems.LAST_LIBRARY, tmpdir)
        storage_path = Path(tmpdir)
        driver = DriverTest(settings)

        # When
        result = driver.evaluate_path(None)

        # Then
        assert result == LibraryStatus(success=True, storage_path=storage_path)
