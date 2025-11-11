# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tagstudio.core.enums import LibraryPrefs
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.refresh import RefreshTracker
from tagstudio.core.utils.types import unwrap

CWD = Path(__file__).parent


@pytest.mark.parametrize("exclude_mode", [True, False])
@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_new_files(library: Library, exclude_mode: bool):
    library_dir = unwrap(library.library_dir)
    # Given
    library.set_prefs(LibraryPrefs.IS_EXCLUDE_LIST, exclude_mode)
    library.set_prefs(LibraryPrefs.EXTENSION_LIST, [".md"])
    registry = RefreshTracker(library=library)
    library.included_files.clear()
    (library_dir / "FOO.MD").touch()

    # Test if the single file was added
    list(registry.refresh_dir(library_dir, force_internal_tools=True))
    assert registry.files_not_in_library == [Path("FOO.MD")]


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_multi_byte_filenames_ripgrep(library: Library):
    assert shutil.which("rg") is not None

    library_dir = unwrap(library.library_dir)
    # Given
    registry = RefreshTracker(library=library)
    library.included_files.clear()
    (library_dir / ".TagStudio").mkdir()
    (library_dir / "こんにちは.txt").touch()
    (library_dir / "em–dash.txt").touch()
    (library_dir / "apostrophe’.txt").touch()
    (library_dir / "umlaute äöü.txt").touch()

    # Test if all files were added with their correct names and without exceptions
    list(registry.refresh_dir(library_dir))
    assert Path("こんにちは.txt") in registry.files_not_in_library
    assert Path("em–dash.txt") in registry.files_not_in_library
    assert Path("apostrophe’.txt") in registry.files_not_in_library
    assert Path("umlaute äöü.txt") in registry.files_not_in_library
