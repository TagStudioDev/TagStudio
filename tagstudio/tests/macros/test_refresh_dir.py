import pathlib
from tempfile import TemporaryDirectory

import pytest
from src.core.enums import LibraryPrefs
from src.core.library import Entry
from src.core.utils.refresh_dir import RefreshDirTracker

CWD = pathlib.Path(__file__).parent


@pytest.mark.parametrize("exclude_mode", [True, False])
@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_new_files(library, exclude_mode):
    # Given
    library.set_prefs(LibraryPrefs.IS_EXCLUDE_LIST, exclude_mode)
    library.set_prefs(LibraryPrefs.EXTENSION_LIST, [".md"])
    registry = RefreshDirTracker(library=library)
    (library.library_dir / "FOO.MD").touch()

    # When
    assert not list(registry.refresh_dir(library.library_dir))

    # Then
    assert registry.files_not_in_library == [pathlib.Path("FOO.MD")]


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_removes_noindex_content(library):
    # Given
    registry = RefreshDirTracker(library=library)

    # create subdirectory with .ts_noindex file in it
    (library.library_dir / "subdir").mkdir()
    (library.library_dir / "subdir" / ".ts_noindex").touch()
    # add entry into library
    entry = Entry(
        path=pathlib.Path("subdir/FOO.MD"),
        folder=library.folder,
        fields=library.default_fields,
    )
    library.add_entries([entry])

    # create its file in noindex directory
    (library.library_dir / entry.path).touch()
    # create another file in the same directory
    (library.library_dir / "subdir" / "test.txt").touch()

    # add non-ignored entry into library
    (library.library_dir / "root.txt").touch()

    # When
    list(registry.refresh_dir(library.library_dir))

    # Then
    # file in noindex folder should be removed
    assert not library.get_path_entry(entry.path)
    # file in index folder should be registered
    assert registry.files_not_in_library == [pathlib.Path("root.txt")]
