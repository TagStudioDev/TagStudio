import pathlib
from tempfile import TemporaryDirectory

import pytest
from src.core.utils.refresh_dir import RefreshDirTracker

CWD = pathlib.Path(__file__).parent


@pytest.mark.parametrize("exclude_mode", [True, False])
@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_new_files(library, exclude_mode):
    # Given
    library.settings.is_exclude_list = exclude_mode
    library.settings.extension_list = [".md"]
    registry = RefreshDirTracker(library=library)
    library.included_files.clear()
    (library.library_dir / "FOO.MD").touch()

    # When
    assert len(list(registry.refresh_dir(library.library_dir))) == 1

    # Then
    assert registry.files_not_in_library == [pathlib.Path("FOO.MD")]
