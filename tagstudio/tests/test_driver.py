from os import makedirs
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.constants import TS_FOLDER_NAME
from src.core.driver import DriverMixin
from src.core.library.alchemy.library import LibraryStatus
from src.core.settings import TSSettings
from src.core.tscacheddata import TSCachedData


class TestDriver(DriverMixin):
    def __init__(self, settings, cache: TSCachedData | None = None):
        self.settings = settings
        if cache:
            self.cache = cache


def test_evaluate_path_empty():
    # Given
    settings = TSSettings(filename="")
    driver = TestDriver(settings)

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == LibraryStatus(success=True)


def test_evaluate_path_missing():
    # Given
    settings = TSSettings(filename="")
    driver = TestDriver(settings)

    # When
    result = driver.evaluate_path("/0/4/5/1/")

    # Then
    assert result == LibraryStatus(success=False, message="Path does not exist.")


def test_evaluate_path_last_lib_not_exists():
    # Given
    settings = TSSettings(filename="")
    cache = TSCachedData.open()
    cache.last_library = "/0/4/5/1/"
    driver = TestDriver(settings, cache)

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == LibraryStatus(success=True, library_path=None, message=None)


def test_evaluate_path_last_lib_present():
    # Given
    with TemporaryDirectory() as tmpdir:
        settings_file = tmpdir + "/test_settings.toml"
        cache = TSCachedData.open(settings_file)
        cache.last_library = tmpdir
        cache.save()

        makedirs(Path(tmpdir) / TS_FOLDER_NAME)
        driver = TestDriver(TSSettings(filename="", open_last_loaded_on_startup=True), cache)

        # When
        result = driver.evaluate_path(None)
        # Then
        assert result == LibraryStatus(success=True, library_path=Path(tmpdir))
