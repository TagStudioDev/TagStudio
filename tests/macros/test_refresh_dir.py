# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

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
    tracker = RefreshTracker(library=library)
    (library_dir / "FOO.MD").touch()

    # Test if the single file was added
    list(tracker.refresh_dir(library_dir, force_internal_tools=True))
    assert tracker._new_paths == {Path("FOO.MD")}
