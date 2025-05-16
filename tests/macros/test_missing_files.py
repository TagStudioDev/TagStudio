from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.missing_files import MissingRegistry

CWD = Path(__file__).parent


# NOTE: Does this test actually work?
@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_missing_files(library: Library):
    registry = MissingRegistry(library=library)

    # touch the file `one/two/bar.md` but in wrong location to simulate a moved file
    (library.library_dir / "bar.md").touch()

    # no files actually exist, so it should return all entries
    assert list(registry.refresh_missing_files()) == [0, 1]

    # neither of the library entries exist
    assert len(registry.missing_file_entries) == 2

    # iterate through two files
    assert list(registry.fix_unlinked_entries()) == [0, 1]

    # `bar.md` should be relinked to new correct path
    results = library.search_library(BrowsingState.from_path("bar.md"), page_size=500)
    assert results[0].path == Path("bar.md")
