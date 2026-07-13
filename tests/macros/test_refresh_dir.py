# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tagstudio.core.constants import IGNORE_NAME
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.refresh import RefreshTracker
from tagstudio.core.utils.types import unwrap

CWD = Path(__file__).parent


@pytest.mark.parametrize("exclude_mode", [True, False])
@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_new_files(library: Library, exclude_mode: bool):
    library_dir = unwrap(library.library_dir)
    # Given
    tracker = RefreshTracker(library=library)
    (library_dir / "FOO.MD").touch()
    (library_dir / IGNORE_NAME).write_text("*.md" if exclude_mode else "*\n!*.md")

    # Test if the single file was added
    list(tracker.refresh_dir(library_dir, force_internal_tools=True))
    assert set(tracker._new_paths) == set([Path(IGNORE_NAME), Path("FOO.MD")])


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_multi_byte_filenames(library: Library):
    library_dir = unwrap(library.library_dir)
    # Given
    tracker = RefreshTracker(library=library)
    (library_dir / ".TagStudio").mkdir()
    (library_dir / "こんにちは.txt").touch()
    (library_dir / "em–dash.txt").touch()
    (library_dir / "apostrophe’.txt").touch()
    (library_dir / "umlaute äöü.txt").touch()

    # Test if all files were added with their correct names and without exceptions
    list(tracker.refresh_dir(library_dir))
    assert Path("こんにちは.txt") in tracker._new_paths
    assert Path("em–dash.txt") in tracker._new_paths
    assert Path("apostrophe’.txt") in tracker._new_paths
    assert Path("umlaute äöü.txt") in tracker._new_paths
