# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

from tagstudio.core.constants import TS_FOLDER_NAME
from tagstudio.core.driver import BaseDriver
from tagstudio.core.library.alchemy.library import OpenLibraryResult
from tagstudio.i18n.translations import Translations


def test_verify_library_path_missing():
    # Given
    driver = BaseDriver()

    # When
    result = driver.verify_library_path("/0/4/5/1/")

    # Then
    assert result == OpenLibraryResult(
        success=False,
        library_path=Path("/0/4/5/1/"),
        error_title=Translations["menu.file.missing_library.title"],
        error_description=Translations.format(
            "menu.file.missing_library.message", library=Path("/0/4/5/1/")
        ),
    )


def test_verify_library_path_not_a_library(tmp_path: Path):
    # Given
    driver = BaseDriver()

    # When
    result = driver.verify_library_path(str(tmp_path), allow_creation=False)

    # Then
    assert result == OpenLibraryResult(
        success=False,
        library_path=tmp_path,
        error_title=Translations["menu.file.missing_library.title"],
        error_description=Translations.format(
            "menu.file.missing_library.message", library=tmp_path
        ),
    )
    assert not (tmp_path / TS_FOLDER_NAME).exists()


def test_verify_library_path_allow_creation(tmp_path: Path):
    # Given
    driver = BaseDriver()

    # When
    result = driver.verify_library_path(str(tmp_path), allow_creation=True)

    # Then
    assert result == OpenLibraryResult(success=True, library_path=tmp_path)


def test_verify_library_path_existing_library(library_dir: Path):
    # Given
    driver = BaseDriver()

    # When
    result = driver.verify_library_path(library_dir, allow_creation=False)

    # Then
    assert result == OpenLibraryResult(success=True, library_path=library_dir)
