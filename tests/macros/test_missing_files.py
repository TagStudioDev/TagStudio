# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.refresh import RefreshTracker
from tagstudio.core.utils.types import unwrap

CWD = Path(__file__).parent


# NOTE: Does this test actually work?
@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_missing_files(library: Library):
    library_dir = unwrap(library.library_dir)
    tracker = RefreshTracker(library)

    # touch the file `one/two/bar.md` but in wrong location to simulate a moved file
    (library_dir / "bar.md").touch()

    # no files actually exist, so it should return all entries
    list(tracker.refresh_dir(library_dir, force_internal_tools=True))
    assert sorted(tracker._missing_paths.values()) == [1, 2]

    # neither of the library entries exist
    assert tracker.missing_files_count == 2

    # iterate through two files
    assert "one/two/bar.md" in tracker._missing_paths
    tracker.fix_unlinked_entries()
    assert "one/two/bar.md" not in tracker._missing_paths

    # `bar.md` should be relinked to new correct path
    results = library.search_library(BrowsingState.from_path("bar.md"), page_size=500)
    entries = library.get_entries(results.ids)
    assert entries[0].path == Path("bar.md")
