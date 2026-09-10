# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage=false

import os
import unicodedata
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tagstudio.core.constants import IGNORE_NAME, TS_FOLDER_NAME
from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.sync import LibrarySyncEngine
from tagstudio.core.utils.types import unwrap


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
def test_sync_unlinked_entries(library: Library):
    """An unlinked entry with one matching file must be found by `relink_unlinked_entries()`."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    # Touch the file "bar.md" but in the wrong location, to simulate a moved file
    (library_dir / "bar.md").touch()

    # Neither library entry ("foo.txt", "one/two/bar.md") exists on disk, so both are unlinked
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.unlinked_entries_count == 2

    # Relinking bar.md should match and relink to the entry that was at "one/two/bar.md"
    list(engine.relink_unlinked_entries())
    assert engine.manual_relink_count == 1
    assert engine.unlinked_entries_count == 1

    results = library.search_library(BrowsingState.from_path("bar.md"), page_size=500)
    entries = library.get_entries(results.ids)
    assert entries[0].path == Path("bar.md")


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
def test_sync_case_sensitivity_aware_relink(library: Library):
    """`find_relink_candidates()` must respect the library's case-sensitivity setting."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "Other").mkdir()
    (library_dir / "Other" / "name.txt").touch()
    library.add_entries([Entry(path=Path("Folder/Name.txt"), fields=[])])

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    unlinked_entry = next(e for e in engine.unlinked_entries if e.path == Path("Folder/Name.txt"))

    library.is_case_sensitive_fs = True
    assert engine.find_relink_candidates(unlinked_entry) == []

    library.is_case_sensitive_fs = False
    engine._filename_to_path_map = None  # Rebuild the index with the new case sensitivity
    assert engine.find_relink_candidates(unlinked_entry) == [Path("Other/name.txt")]


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
def test_sync_duplicate_case_collision_treated_as_unlinked(library: Library):
    """A duplicate entry displaced by a case-insensitive collision must be treated as unlinked."""
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)
    library.is_case_sensitive_fs = False  # Force a collision using a case difference

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

    # The dupe ID should be marked as unlinked, and the original ID should not
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    unlinked_ids = {e.id for e in engine.unlinked_entries}
    assert dupe_id in unlinked_ids
    assert original_id not in unlinked_ids

    # Removing the duplicate entry shouldn't remove the original from the cache
    engine.unlinked_entries = [e for e in engine.unlinked_entries if e.id == dupe_id]
    engine.remove_unlinked_entries()
    assert cache.get(path_key) == original_id
    assert library.duplicate_path_entry_ids == []


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_moved_file(library: Library):
    """A moved file (same filename + stats, different path) must auto-relink to its entry."""
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
def test_sync_auto_relink_moved_file_ambiguous(library: Library):
    """Two equally-matching candidates (same filename + stats) must not auto-relink.

    NOTE: This may change in the future as capability expands.
    """
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
def test_sync_auto_relink_moved_file_stat_mismatch(library: Library):
    """A file with (same filename, different stats) must not auto-relink.

    NOTE: This is a limitation of the current auto-relinking system, NOT a design principle.
    """
    library_dir = unwrap(library.library_dir)
    engine = LibrarySyncEngine(library=library)

    (library_dir / "notmoved.txt").touch()
    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    list(engine.save_new_entries())

    (library_dir / "notmoved.txt").unlink()
    (library_dir / "sub").mkdir()
    (library_dir / "sub" / "notmoved.txt").touch()

    list(engine.sync_dir(library_dir, force_internal_scanner=True))
    assert engine.relinked_entries_count == 0
    assert Path("sub/notmoved.txt") in engine.new_paths
    assert Path("notmoved.txt") in {e.path for e in engine.unlinked_entries}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_sync_auto_relink_renamed_file(library: Library):
    """A renamed file (different filename, same stats) must auto-relink to its entry."""
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
def test_sync_auto_relink_renamed_file_ambiguous(library: Library):
    """Two equally-matching candidates (different filenames, same stats) must not auto-relink.

    NOTE: This may be automated in the future, but for now differs to the user's judgement.
    """
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
def test_sync_auto_relink_moved_and_renamed_together(library: Library):
    """A moved file and a renamed file in the same sync must each auto-relink via their own pass."""
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
