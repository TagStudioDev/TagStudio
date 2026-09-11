# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage=false

import os
import unicodedata
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from tagstudio.core.constants import IGNORE_NAME, TS_FOLDER_NAME
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.sync import LibrarySyncEngine
from tagstudio.core.utils.types import unwrap

# NOTE: Case numbers are described in the Library documentation.


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_new_files(library: Library):
    """New files that aren't excluded by an ignore pattern must be picked up as new."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)
    (library_dir / "foo.md").touch()
    (library_dir / "bar.txt").touch()
    ts_ignore_path = library_dir / TS_FOLDER_NAME / IGNORE_NAME
    ts_ignore_path.parent.mkdir(parents=True, exist_ok=True)
    ts_ignore_path.write_text("*.md")

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert set(engine.new_paths) == {Path("bar.txt")}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_multi_byte_filenames(library: Library):
    """Multi-byte and accented Unicode filenames must be scanned and added without errors."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)
    (library_dir / ".TagStudio").mkdir()
    (library_dir / "こんにちは.txt").touch()
    (library_dir / "em–dash.txt").touch()
    (library_dir / "apostrophe’.txt").touch()
    (library_dir / "umlaute äöü.txt").touch()

    list(engine.sync_dir(library_dir))
    assert Path("こんにちは.txt") in engine.new_paths
    assert Path("em–dash.txt") in engine.new_paths
    assert Path("apostrophe’.txt") in engine.new_paths
    assert Path("umlaute äöü.txt") in engine.new_paths


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_nfd_nfc_false_positive(library: Library):
    """A file reappearing in a different Unicode form must not look like a new/duplicate entry."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    nfc_name = unicodedata.normalize("NFC", "SKÅL.txt")
    nfd_name = unicodedata.normalize("NFD", "SKÅL.txt")
    assert nfc_name != nfd_name

    (library_dir / nfc_name).touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    # Simulate the file later showing up in NFD form, as if the filesystem was changed
    (library_dir / nfc_name).unlink()
    (library_dir / nfd_name).touch()

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.new_paths == []
    assert len(engine.paths_to_restat) == 1
    assert engine.unlinked_entries_count == 2


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_cache_pruned_on_remove(library: Library):
    """Removing an unlinked entry must prune the path cache."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    tracked_path = Path("tracked.txt")
    (library_dir / tracked_path).touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    (library_dir / tracked_path).unlink()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    tracked_entry = next(e for e in engine.unlinked_entries if e.path == tracked_path)

    cache = library.get_or_build_path_cache()
    assert tracked_path in cache

    # Only an explicit removal should prune the cache
    engine.unlinked_entries = [tracked_entry]
    engine.remove_unlinked_entries()
    assert tracked_path not in cache

    # A different file at the same path afterwards should be treated as new
    (library_dir / tracked_path).touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.new_paths == [tracked_path]


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_signals_repair_phase_when_entries_are_unlinked(library: Library):
    """`sync_dir()` must yield a (-1, -1) signal before repair work when entries are unlinked."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    # The baseline entries never existed on disk, so they're always unlinked here
    progress = list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert (-1, -1) in progress


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_duplicate_case_collision_merged(library: Library):
    """A duplicate entry displaced by a case-insensitive collision must be merged automatically."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)
    library.is_case_sensitive_fs = False  # Force a case-insensitive collision

    (library_dir / "Dupe").mkdir()
    (library_dir / "Dupe" / "photo.jpg").touch()
    entry_a_id, entry_b_id = library.add_entries(
        [
            Entry(path=Path("Dupe/photo.jpg"), fields=[]),
            Entry(path=Path("Dupe/PHOTO.JPG"), fields=[]),
        ]
    )

    cache = library.get_or_build_path_cache()
    path_key = Path("dupe/photo.jpg")  # Case-insensitive + NFD
    assert library.duplicate_path_entry_ids is not None
    assert len(library.duplicate_path_entry_ids) == 1
    dupe_id = library.duplicate_path_entry_ids[0]
    original_id = entry_b_id if dupe_id == entry_a_id else entry_a_id
    assert cache.get(path_key) == original_id

    entries_before = library.entries_count
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 1
    assert engine.relinked_entries[0].id == dupe_id
    assert dupe_id not in {e.id for e in engine.unlinked_entries}
    # A merge deletes the duplicate outright, rather than just reassigning its path
    assert library.entries_count == entries_before - 1
    assert cache.get(path_key) == original_id
    assert library.duplicate_path_entry_ids == []


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_merges_nfc_nfd_duplicate(library: Library):
    """A duplicate entry differing only by Unicode form must be merged automatically.

    PathType always normalizes to NFD, so this test uses raw SQL to simulate legacy data
    from before that rule existed.
    """
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    nfc_name = unicodedata.normalize("NFC", "SKÅL.txt")
    nfd_name = unicodedata.normalize("NFD", "SKÅL.txt")
    assert nfc_name != nfd_name

    # The real file lands in NFD form, as most filesystems store it regardless of input form
    (library_dir / nfd_name).touch()
    entry_a_id, entry_b_id = library.add_entries(
        [
            Entry(path=Path(nfd_name), fields=[]),
            Entry(path=Path("placeholder.txt"), fields=[]),
        ]
    )
    with Session(library.engine) as session:
        session.execute(
            text("UPDATE entries SET path = :path WHERE id = :id"),
            {"path": nfc_name, "id": entry_b_id},
        )
        session.commit()
    library.path_cache = None  # Force a rebuild to pick up the raw SQL change

    library.get_or_build_path_cache()
    assert library.duplicate_path_entry_ids is not None
    assert len(library.duplicate_path_entry_ids) == 1
    dupe_id = library.duplicate_path_entry_ids[0]
    kept_id = entry_b_id if dupe_id == entry_a_id else entry_a_id

    entries_before = library.entries_count
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 1
    assert engine.relinked_entries[0].id == dupe_id
    assert dupe_id not in {e.id for e in engine.unlinked_entries}
    assert library.entries_count == entries_before - 1
    assert unwrap(library.get_entry_full(kept_id)).id == kept_id


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_respects_case_sensitivity(library: Library):
    """The filename-only fallback pass must respect the library's case-sensitivity setting."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "Other").mkdir()
    (library_dir / "Other" / "name.txt").touch()
    library.add_entries([Entry(path=Path("Folder/Name.txt"), fields=[])])

    library.is_case_sensitive_fs = True
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("Folder/Name.txt") in {e.path for e in engine.unlinked_entries}

    library.is_case_sensitive_fs = False
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 1
    assert engine.relinked_entries[0].path == Path("Folder/Name.txt")
    assert library.get_entry_id_from_path(Path("Other/name.txt")) >= 0


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_modified_file_stays_linked(library: Library):
    """[Case #0] Modifying a file's content in place must not create an unlinked entry."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "stable.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    (library_dir / "stable.txt").write_text("modified content")

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert Path("stable.txt") not in {e.path for e in engine.unlinked_entries}
    assert engine.new_paths == []
    assert len(engine.paths_to_restat) == 1


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_deleted_file(library: Library):
    """[Case #1] A deleted file with no candidates anywhere must not auto-relink."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "gone.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    (library_dir / "gone.txt").unlink()

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert engine.new_paths == []
    assert Path("gone.txt") in {e.path for e in engine.unlinked_entries}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_moved_and_renamed_file_modified(library: Library):
    """[Case #2] A moved, renamed, and modified file must not auto-relink."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "original_name.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    (library_dir / "original_name.txt").unlink()
    (library_dir / "sub").mkdir()
    (library_dir / "sub" / "renamed.txt").write_text("different content, different size")

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("sub/renamed.txt") in engine.new_paths
    assert Path("original_name.txt") in {e.path for e in engine.unlinked_entries}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_moved_and_renamed_file(library: Library):
    """[Case #3] A single file that is both moved and renamed must still auto-relink."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "original_name.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    original_id = library.get_entry_id_from_path(Path("original_name.txt"))
    assert original_id >= 0

    (library_dir / "sub").mkdir()
    (library_dir / "original_name.txt").rename(library_dir / "sub" / "renamed.txt")

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.new_paths == []
    assert engine.relinked_entries_count == 1
    assert engine.relinked_entries[0].id == original_id
    assert library.get_entry_id_from_path(Path("sub/renamed.txt")) == original_id
    assert library.get_entry_id_from_path(Path("original_name.txt")) == -1


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_single_entry_multiple_moved_and_renamed_files(library: Library):
    """[Case #4] A single entry must not auto-relink to 2+ equally-matching moved+renamed files.

    NOTE: This may change in the future as capability expands.
    """
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "original_name.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    original_stat = (library_dir / "original_name.txt").stat()

    (library_dir / "original_name.txt").unlink()
    (library_dir / "a").mkdir()
    (library_dir / "b").mkdir()
    (library_dir / "a" / "renamed1.txt").touch()
    (library_dir / "b" / "renamed2.txt").touch()
    os.utime(library_dir / "a" / "renamed1.txt", (original_stat.st_atime, original_stat.st_mtime))
    os.utime(library_dir / "b" / "renamed2.txt", (original_stat.st_atime, original_stat.st_mtime))

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("a/renamed1.txt") in engine.new_paths
    assert Path("b/renamed2.txt") in engine.new_paths
    assert Path("original_name.txt") in {e.path for e in engine.unlinked_entries}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_multiple_entries_one_moved_and_renamed_file(library: Library):
    """[Case #5] Two or more entries must not auto-relink to one matching moved+renamed file."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "a").mkdir()
    (library_dir / "b").mkdir()
    (library_dir / "a" / "one.txt").touch()
    (library_dir / "b" / "two.txt").touch()
    st = (library_dir / "a" / "one.txt").stat()
    os.utime(library_dir / "b" / "two.txt", (st.st_atime, st.st_mtime))

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    (library_dir / "a" / "one.txt").unlink()
    (library_dir / "b" / "two.txt").unlink()
    (library_dir / "c").mkdir()
    (library_dir / "c" / "renamed.txt").touch()
    os.utime(library_dir / "c" / "renamed.txt", (st.st_atime, st.st_mtime))

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("c/renamed.txt") in engine.new_paths
    unlinked_paths = {e.path for e in engine.unlinked_entries}
    assert Path("a/one.txt") in unlinked_paths
    assert Path("b/two.txt") in unlinked_paths


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_moved_file_modified(library: Library):
    """[Case #6] A moved + modified file must still auto-relink by its unique filename."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "notmoved.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    original_id = library.get_entry_id_from_path(Path("notmoved.txt"))
    assert original_id >= 0

    (library_dir / "notmoved.txt").unlink()
    (library_dir / "sub").mkdir()
    (library_dir / "sub" / "notmoved.txt").write_text("different content, different size")

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.new_paths == []
    assert engine.relinked_entries_count == 1
    assert engine.relinked_entries[0].id == original_id
    assert library.get_entry_id_from_path(Path("sub/notmoved.txt")) == original_id
    # The original path should no longer be associated with an entry
    assert library.get_entry_id_from_path(Path("notmoved.txt")) == -1


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_moved_file(library: Library):
    """[Case #7] A moved file (same filename + stats, different path) must auto-relink."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "moveme.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    original_id = library.get_entry_id_from_path(Path("moveme.txt"))
    assert original_id >= 0

    (library_dir / "sub").mkdir()
    (library_dir / "moveme.txt").rename(library_dir / "sub" / "moveme.txt")

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.new_paths == []
    assert engine.relinked_entries_count == 1
    assert engine.relinked_entries[0].id == original_id
    assert Path("sub/moveme.txt") not in {e.path for e in engine.unlinked_entries}
    assert library.get_entry_id_from_path(Path("sub/moveme.txt")) == original_id
    # The original path should no longer be associated with an entry
    assert library.get_entry_id_from_path(Path("moveme.txt")) == -1


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_moved_files_same_names(library: Library):
    """[Case #7] A file candidate with same name + different stats must not block the real match."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "photo.jpg").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    original_id = library.get_entry_id_from_path(Path("photo.jpg"))
    assert original_id >= 0
    original_stat = (library_dir / "photo.jpg").stat()

    (library_dir / "a").mkdir()
    (library_dir / "b").mkdir()
    (library_dir / "photo.jpg").rename(library_dir / "a" / "photo.jpg")
    (library_dir / "b" / "photo.jpg").touch()
    # Ensure a different mtime than "a/photo.jpg"
    os.utime(
        library_dir / "b" / "photo.jpg", (original_stat.st_atime, original_stat.st_mtime + 100)
    )

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 1
    assert engine.relinked_entries[0].id == original_id
    assert library.get_entry_id_from_path(Path("a/photo.jpg")) == original_id
    assert Path("b/photo.jpg") in engine.new_paths


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_single_entry_multiple_moved_files(library: Library):
    """[Case #8] A single entry must not auto-relink to multiple equally-matching file candidates.

    NOTE: This may change in the future as capability expands.
    """
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "photo.jpg").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    assert library.get_entry_id_from_path(Path("photo.jpg")) >= 0
    original_stat = (library_dir / "photo.jpg").stat()

    (library_dir / "a").mkdir()
    (library_dir / "b").mkdir()
    (library_dir / "photo.jpg").rename(library_dir / "a" / "photo.jpg")
    (library_dir / "b" / "photo.jpg").touch()
    os.utime(library_dir / "b" / "photo.jpg", (original_stat.st_atime, original_stat.st_mtime))

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("a/photo.jpg") in engine.new_paths
    assert Path("b/photo.jpg") in engine.new_paths
    assert Path("photo.jpg") in {e.path for e in engine.unlinked_entries}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_multiple_entries_one_moved_file(library: Library):
    """[Case #9] Two or more entries must not auto-relink to one matching file candidate."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "a").mkdir()
    (library_dir / "b").mkdir()
    (library_dir / "a" / "dupe.txt").touch()
    (library_dir / "b" / "dupe.txt").touch()
    st = (library_dir / "a" / "dupe.txt").stat()
    os.utime(library_dir / "b" / "dupe.txt", (st.st_atime, st.st_mtime))

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    (library_dir / "a" / "dupe.txt").unlink()
    (library_dir / "b" / "dupe.txt").unlink()
    (library_dir / "c").mkdir()
    (library_dir / "c" / "dupe.txt").touch()
    os.utime(library_dir / "c" / "dupe.txt", (st.st_atime, st.st_mtime))

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("c/dupe.txt") in engine.new_paths
    unlinked_paths = {e.path for e in engine.unlinked_entries}
    assert Path("a/dupe.txt") in unlinked_paths
    assert Path("b/dupe.txt") in unlinked_paths


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_renamed_file_modified(library: Library):
    """[Case #10] A renamed file with different stats must not auto-relink."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "original_name.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    (library_dir / "original_name.txt").unlink()
    (library_dir / "renamed_and_modified.txt").write_text("different content, different size")

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("renamed_and_modified.txt") in engine.new_paths
    assert Path("original_name.txt") in {e.path for e in engine.unlinked_entries}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_renamed_file(library: Library):
    """[Case #11] A renamed file (different filename, same stats) must auto-relink to its entry."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "original_name.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    original_id = library.get_entry_id_from_path(Path("original_name.txt"))
    assert original_id >= 0

    (library_dir / "original_name.txt").rename(library_dir / "renamed.txt")

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.new_paths == []
    assert engine.relinked_entries_count == 1
    assert engine.relinked_entries[0].id == original_id
    assert Path("renamed.txt") not in {e.path for e in engine.unlinked_entries}
    assert library.get_entry_id_from_path(Path("renamed.txt")) == original_id
    # The original path should no longer be associated with an entry
    assert library.get_entry_id_from_path(Path("original_name.txt")) == -1


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_single_entry_multiple_renamed_files(library: Library):
    """[Case #12] A single entry must not auto-relink to 2+ matched renamed files."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "original_name.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    original_stat = (library_dir / "original_name.txt").stat()

    (library_dir / "original_name.txt").unlink()
    (library_dir / "renamed1.txt").touch()
    (library_dir / "renamed2.txt").touch()
    os.utime(library_dir / "renamed1.txt", (original_stat.st_atime, original_stat.st_mtime))
    os.utime(library_dir / "renamed2.txt", (original_stat.st_atime, original_stat.st_mtime))

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("renamed1.txt") in engine.new_paths
    assert Path("renamed2.txt") in engine.new_paths
    assert Path("original_name.txt") in {e.path for e in engine.unlinked_entries}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_multiple_entries_one_renamed_file(library: Library):
    """[Case #13] Two or more entries must not auto-relink to one matching renamed file."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "one.txt").touch()
    (library_dir / "two.txt").touch()
    st = (library_dir / "one.txt").stat()
    os.utime(library_dir / "two.txt", (st.st_atime, st.st_mtime))

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    (library_dir / "one.txt").unlink()
    (library_dir / "two.txt").unlink()
    (library_dir / "renamed.txt").touch()
    os.utime(library_dir / "renamed.txt", (st.st_atime, st.st_mtime))

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("renamed.txt") in engine.new_paths
    unlinked_paths = {e.path for e in engine.unlinked_entries}
    assert Path("one.txt") in unlinked_paths
    assert Path("two.txt") in unlinked_paths


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_separate_moved_and_renamed_files(library: Library):
    """[Cases #7, #11] Two separate files, one moved and one renamed, must each auto-relink."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "moveme.txt").touch()
    (library_dir / "rename_orig.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    moved_id = library.get_entry_id_from_path(Path("moveme.txt"))
    renamed_id = library.get_entry_id_from_path(Path("rename_orig.txt"))
    assert moved_id >= 0
    assert renamed_id >= 0

    (library_dir / "sub").mkdir()
    (library_dir / "moveme.txt").rename(library_dir / "sub" / "moveme.txt")
    (library_dir / "rename_orig.txt").rename(library_dir / "rename_new.txt")

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.new_paths == []
    assert engine.relinked_entries_count == 2
    assert {e.id for e in engine.relinked_entries} == {moved_id, renamed_id}
    assert library.get_entry_id_from_path(Path("sub/moveme.txt")) == moved_id
    assert library.get_entry_id_from_path(Path("rename_new.txt")) == renamed_id


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_matches_entry_without_stored_stats_by_filename(library: Library):
    """An entry with no stored stats must auto-relink to a single matching filename."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)
    library.add_entries([Entry(path=Path("legacy.txt"), fields=[])])
    original_id = library.get_entry_id_from_path(Path("legacy.txt"))
    assert original_id >= 0

    (library_dir / "sub").mkdir()
    (library_dir / "sub" / "legacy.txt").touch()

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.new_paths == []
    assert engine.relinked_entries_count == 1
    assert engine.relinked_entries[0].id == original_id
    assert Path("legacy.txt") not in {e.path for e in engine.unlinked_entries}
    assert library.get_entry_id_from_path(Path("sub/legacy.txt")) == original_id
    # The original path should no longer be associated with an entry
    assert library.get_entry_id_from_path(Path("legacy.txt")) == -1


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_skips_ambiguous_entry_without_stored_stats(library: Library):
    """An entry with no stored stats must not auto-relink to 2+ files with the same name."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)
    library.add_entries([Entry(path=Path("legacy.txt"), fields=[])])

    (library_dir / "a").mkdir()
    (library_dir / "b").mkdir()
    (library_dir / "a" / "legacy.txt").touch()
    (library_dir / "b" / "legacy.txt").touch()

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("a/legacy.txt") in engine.new_paths
    assert Path("b/legacy.txt") in engine.new_paths
    assert Path("legacy.txt") in {e.path for e in engine.unlinked_entries}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_cancel_skips_unlinked_finalization(library: Library):
    """A cancelled `sync_dir()` call must not mark any entries as unlinked."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "a.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    baseline_unlinked_count = engine.unlinked_entries_count

    # Case where sync is cancelled before this scan even starts
    engine.cancelled = True
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.unlinked_entries_count == baseline_unlinked_count
    assert engine.new_paths == []


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_cancel_skips_duplicate_merge(library: Library):
    """Cancelling right after the scan must stop duplicate merging before it starts."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)
    library.is_case_sensitive_fs = False  # Force a collision using a case difference

    (library_dir / "Dupe").mkdir()
    (library_dir / "Dupe" / "photo.jpg").touch()
    library.add_entries(
        [
            Entry(path=Path("Dupe/photo.jpg"), fields=[]),
            Entry(path=Path("Dupe/PHOTO.JPG"), fields=[]),
        ]
    )
    library.get_or_build_path_cache()
    assert library.duplicate_path_entry_ids is not None
    assert len(library.duplicate_path_entry_ids) == 1
    dupe_id = library.duplicate_path_entry_ids[0]

    # Cancel right as the repair phase signal comes through, before merging actually runs
    generator = engine.sync_dir(library_dir, force_internal_scanner=True)
    for progress in generator:
        if progress == (-1, -1):
            engine.cancelled = True
            break
    list(generator)

    assert engine.relinked_entries_count == 0
    assert dupe_id in {e.id for e in engine.unlinked_entries}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_cancel_skips_remaining_relink_passes(library: Library):
    """Cancelling right after the scan must let Pass 1 finish, but stop before Pass 2."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "moveme.txt").touch()
    (library_dir / "original_name.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())
    moved_id = library.get_entry_id_from_path(Path("moveme.txt"))
    renamed_id = library.get_entry_id_from_path(Path("original_name.txt"))

    (library_dir / "sub").mkdir()
    (library_dir / "moveme.txt").rename(library_dir / "sub" / "moveme.txt")  # Pass 1 match
    (library_dir / "original_name.txt").rename(library_dir / "renamed.txt")  # Pass 2 match

    # Cancel right as the repair phase signal comes through, before relinking actually runs
    generator = engine.sync_dir(library_dir, force_internal_scanner=True)
    for progress in generator:
        if progress == (-1, -1):
            engine.cancelled = True
            break
    list(generator)

    relinked_ids = {e.id for e in engine.relinked_entries}
    assert moved_id in relinked_ids
    assert renamed_id not in relinked_ids
    assert Path("renamed.txt") in engine.new_paths


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_cancel_skips_save_new_entries(library: Library):
    """A cancelled `save_new_entries()` call must not save any new entries."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    baseline_count = library.entries_count

    (library_dir / "f0.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.new_paths == [Path("f0.txt")]

    engine.cancelled = True
    list(engine.save_new_entries())
    assert library.entries_count == baseline_count
    assert engine.new_paths == [Path("f0.txt")]


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_cancel_skips_sync_entry_stats(library: Library):
    """A cancelled `sync_entry_stats()` call must not touch `paths_to_restat`."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "f0.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    # A second scan finds the same file again, marking it for a restat
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert len(engine.paths_to_restat) == 1
    expected = list(engine.paths_to_restat)

    engine.cancelled = True
    list(engine.sync_entry_stats())
    assert engine.paths_to_restat == expected
