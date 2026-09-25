# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

from PySide6.QtCore import QSettings

from tagstudio.core.driver import DriverMixin
from tagstudio.core.enums import AppCacheItems
from tagstudio.core.library.alchemy.library import OpenLibraryResult
from tagstudio.i18n.translations import Translations
from tagstudio.qt.app_settings import AppSettings


# TODO: Remove Qt-specific things from this base driver text
class TestBaseDriver(DriverMixin):
    def __init__(self, settings: AppSettings, cache: QSettings):
        self.settings = settings
        self.cached_values = cache


def test_evaluate_path_empty():
    # Given
    driver = TestBaseDriver(AppSettings(), QSettings())

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == OpenLibraryResult(success=True)


def test_evaluate_path_missing():
    # Given
    driver = TestBaseDriver(AppSettings(), QSettings())

    # When
    result = driver.evaluate_path("/0/4/5/1/")

    # Then
    assert result == OpenLibraryResult(
        success=False,
        error_title=Translations["menu.file.missing_library.title"],
        error_description=Translations.format(
            "menu.file.missing_library.message", library="/0/4/5/1/"
        ),
    )


def test_evaluate_path_last_lib_not_exists():
    # Given
    cache = QSettings()
    cache.setValue(AppCacheItems.LAST_LIBRARY, "/0/4/5/1/")
    driver = TestBaseDriver(AppSettings(), cache)

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == OpenLibraryResult(success=True, library_path=None)


def test_evaluate_path_last_lib_present(library_dir: Path):
    # Given
    cache_file = library_dir / "test_settings.ini"
    cache = QSettings(str(cache_file), QSettings.Format.IniFormat)
    cache.setValue(AppCacheItems.LAST_LIBRARY, library_dir)
    cache.sync()

    settings = AppSettings()
    settings.open_last_loaded_on_startup = True

    driver = TestBaseDriver(settings, cache)

    # When
    result = driver.evaluate_path(None)

    # Then
    assert result == OpenLibraryResult(success=True, library_path=library_dir)
