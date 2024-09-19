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
    library.set_prefs(LibraryPrefs.EXTENSION_LIST, ["md"])
    registry = RefreshDirTracker(library=library)

    folder = library.get_folders()[0]
    (folder.path / "FOO.MD").touch()

    # When
    list(registry.refresh_dirs(folder))

    # Then
    assert registry.files_not_in_library == [(folder, pathlib.Path("FOO.MD"))]


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_refresh_removes_noindex_content(library):
    # Given
    registry = RefreshDirTracker(library=library)

    folder = library.get_folders()[0]

    # create subdirectory with .ts_noindex file in it
    (folder.path / "subdir").mkdir()
    (folder.path / "subdir" / ".ts_noindex").touch()

    # add entry into library
    entry = Entry(
        path=pathlib.Path("subdir/FOO.MD"),
        folder=library.get_folders()[0],
        fields=library.default_fields,
    )

    # create its file in noindex directory
    assert entry.folder
    assert entry.folder.path
    entry.absolute_path.touch()
    library.add_entries([entry])

    # create another file in the same directory
    (folder.path / "subdir" / "test.txt").touch()

    # add non-ignored entry into library
    (folder.path / "root.txt").touch()

    # When
    list(registry.refresh_dirs(folder))

    # Then
    # file in noindex folder should be removed
    assert not library.get_path_entry(entry.path)
    # file in index folder should be registered
    assert registry.files_not_in_library == [(folder, pathlib.Path("root.txt"))]
