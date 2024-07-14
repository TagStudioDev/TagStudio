import pathlib
from tempfile import TemporaryDirectory

import pytest
from src.core.utils.refresh_dir import RefreshDirTracker

CWD = pathlib.Path(__file__).parent


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_new_files(library):
    registry = RefreshDirTracker(library=library)

    # touch new files to simulate new files
    (library.library_dir / "foo.md").touch()

    assert not list(registry.refresh_dir())

    assert registry.files_not_in_library == [pathlib.Path("foo.md")]
