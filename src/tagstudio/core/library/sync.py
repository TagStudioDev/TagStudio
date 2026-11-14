# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import posixpath
from collections.abc import Callable, Hashable, Iterator
from dataclasses import dataclass, field
from datetime import datetime as dt
from pathlib import Path
from time import sleep, time

import structlog

from tagstudio.core.library.alchemy.library import FileEntryTuple, Library, StatTuple
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.library.scanners import scan_paths
from tagstudio.core.utils.normalization import is_file, norm_str
from tagstudio.core.utils.stat import get_date_created, get_date_modified, get_file_size
from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger(__name__)

# Yield progress this often during a loop to avoid overwhelming the UI.
# TODO: Look into whether or not this can be handled on the UI side.
YIELD_INTERVAL_SECONDS = 0.068


@dataclass
class LibrarySyncEngine:
    """Keeps a Library's entries in sync with its content directories on disk."""

    library: Library
    cancelled: bool = False
    new_paths: dict[str, StatTuple] = field(default_factory=dict)
    paths_to_restat: list[tuple[int, str]] = field(default_factory=list)
    relinked_entries: list[FileEntryTuple] = field(default_factory=list)
    unlinked_entries: list[FileEntryTuple] = field(default_factory=list)

    @property
    def new_file_count(self) -> int:
        return len(self.new_paths)

    @property
    def restat_count(self) -> int:
        return len(self.paths_to_restat)

    @property
    def unlinked_entries_count(self) -> int:
        return len(self.unlinked_entries)

    @property
    def relinked_entries_count(self) -> int:
        return len(self.relinked_entries)

    def reset(self) -> None:
        """Clear this engine's scan results."""
        self.new_paths = {}
        self.paths_to_restat = []
        self.unlinked_entries = []
        self.relinked_entries = []

    def sync_dir(
        self, library_dir: Path, force_internal_scanner: bool = False
    ) -> Iterator[tuple[int, int]]:
        """Scan library directory for files, then reconcile them against the Library's entries.

        - New files on disk have their stats saved and are skipped if `stat()` fails
        - Entries with no matching file on disk are marked as "unlinked"
            - Automatically relink to appropriate new files on disk where possible
        - Remaining new files on disk are left for `save_new_entries()` to add as entries
        - Remaining unlinked entries are tracked for manual review.

        Yields (searched_count, found_count)

        Args:
            library_dir (Path): The library directory.
            force_internal_scanner (bool): Option to force the use of the internal scanner
                (i.e. wcmatch) instead of third-party tools found on the system (i.e. ripgrep).
        """
        self.reset()
        self.cancelled = False

        cache = self.library.get_or_build_path_cache()
        unvisited = dict(cache)  # Copy the cache in case it's modified during the scan
        ignore_patterns = Ignore.get_patterns(library_dir)

        start_time = time()
        start_time_loop = time()
        count = 0
        for raw_path in scan_paths(library_dir, ignore_patterns, force_internal_scanner):
            if self.cancelled:
                break
            count += 1
            path = raw_path.as_posix()
            key = self.library.path_cache_key(path)
            entry_id = cache.get(key)
            if entry_id is not None:
                unvisited.pop(key, None)
                self.paths_to_restat.append((entry_id, path))
            else:
                try:
                    file_stat = (library_dir / path).stat()
                    self.new_paths[path] = StatTuple(
                        get_date_created(file_stat),
                        get_date_modified(file_stat),
                        get_file_size(file_stat),
                    )
                except OSError as e:
                    logger.error("[Sync] Could not stat new file", path=path, error=e)

            if (time() - start_time_loop) > YIELD_INTERVAL_SECONDS:
                yield count, len(self.new_paths)
                # NOTE: sleep(0) will let the UI thread acquire the GIL before its required here.
                sleep(0)
                start_time_loop = time()

        # NOTE: Ignored files are skipped during the scan.
        missing_entries: list[FileEntryTuple] = []
        if not self.cancelled:
            for entry in self.library.get_file_entry_tuples(list(unvisited.values())):
                if self.cancelled:
                    break
                if not is_file(library_dir / entry.path):
                    missing_entries.append(entry)

        if self.cancelled:
            yield count, len(self.new_paths)
            logger.info("[Sync] Directory scan cancelled", path=library_dir, files_scanned=count)
            return

        self.unlinked_entries = missing_entries
        if self.library.duplicate_path_entry_ids:
            self.unlinked_entries += self.library.get_file_entry_tuples(
                self.library.duplicate_path_entry_ids
            )

        if self.unlinked_entries:
            yield -1, -1  # Signals the UI that repair work is starting

        # Any (rare) duplicate entries are merged first, then the normal relinking process
        self._merge_duplicate_path_entries(cache)
        self._auto_relink_matched_entries(cache)

        yield count, len(self.new_paths)
        logger.info(
            "[Sync] Directory scan complete",
            path=library_dir,
            duration=(time() - start_time),
            files_scanned=count,
            new_files=len(self.new_paths),
            unlinked_entries=len(self.unlinked_entries),
            relinked_entries=len(self.relinked_entries),
        )

    def save_new_entries(self) -> Iterator[int]:
        """Save the paths found on disk that don't have a Library entry yet."""
        batch_size = 1000

        # Sort new files by date modified before adding to the library
        sorted_paths = sorted(self.new_paths, key=lambda path: self.new_paths[path].date_modified)

        index = 0
        while index < len(sorted_paths):
            if self.cancelled:
                break
            yield index
            end = min(len(sorted_paths), index + batch_size)
            batch = sorted_paths[index:end]
            entries = []
            for entry_path in batch:
                file_stat = self.new_paths[entry_path]
                entries.append(
                    Entry(
                        path=Path(entry_path),
                        fields=[],
                        date_created=file_stat.date_created,
                        date_modified=file_stat.date_modified,
                        file_size=file_stat.file_size,
                        date_added=dt.now(),
                    )
                )
            self.library.add_entries(entries)  # Path cache is updated in the library
            index = end
        # Saved entries are removed from new_paths
        self.new_paths = {path: self.new_paths[path] for path in sorted_paths[index:]}

    def sync_entry_stats(self) -> Iterator[int]:
        """Refresh cached os.stat() metadata for entries already known to the Library."""
        batch_size = 5000
        start_time = time()
        updated_count = 0

        index = 0
        while index < len(self.paths_to_restat):
            if self.cancelled:
                break
            yield index
            end = min(len(self.paths_to_restat), index + batch_size)
            updated_count += self.library.refresh_entries_stats(self.paths_to_restat[index:end])
            index = end
        self.paths_to_restat = self.paths_to_restat[index:]
        logger.info(
            "[Sync] File entry stat sync cancelled"
            if self.cancelled
            else "[Sync] File entry stat sync complete",
            duration=(time() - start_time),
            entries_checked=index,
            entries_updated=updated_count,
        )

    def _apply_relink(self, entry: FileEntryTuple, new_path: str, cache: dict[str, int]) -> bool:
        """Assign `new_path` to the `entry`, merging into a single entry if entries exist for both.

        Returns:
            bool: True if the relink was successful.
        """
        new_key = self.library.path_cache_key(new_path)

        existing_id = cache.get(new_key)
        if existing_id is not None and existing_id != entry.id:
            # Merge both entries into one with the single path
            target = unwrap(self.library.get_entry_full(existing_id))
            source = unwrap(self.library.get_entry_full(entry.id))
            return self.library.merge_entries(source, target)
        return self.library.update_entry_path(entry.id, Path(new_path))

    def _relink_unique_matches(
        self,
        cache: dict[str, int],
        key_of_entry: Callable[[FileEntryTuple], Hashable],
        key_of_path: Callable[[str], Hashable],
        log_message: str,
    ) -> None:
        """Relink entries to new paths that share a unique key for matching.

        Args:
            cache (dict[str, int]): Path cache, forwarded to `_apply_relink()`.
            key_of_entry (Callable[[FileEntryTuple], Hashable]): Computes an entry's match key.
            key_of_path (Callable[[str], Hashable]): Computes a path's match key.
            log_message (str): Logged on each successful relink in this pass.
        """
        if not self.new_paths or not self.unlinked_entries:
            return  # Nothing to match against

        by_key: dict[Hashable, list[FileEntryTuple]] = {}  # Key -> entries sharing it
        for entry in self.unlinked_entries:
            by_key.setdefault(key_of_entry(entry), []).append(entry)

        paths_by_key: dict[Hashable, list[str]] = {}  # Key -> candidate paths sharing it
        for path in self.new_paths:
            paths_by_key.setdefault(key_of_path(path), []).append(path)

        relinked: list[FileEntryTuple] = []
        for key, candidate_paths in paths_by_key.items():  # Check each key for a unique pairing
            candidates = by_key.get(key, [])
            if len(candidates) != 1 or len(candidate_paths) != 1:  # Ambiguous case
                continue

            entry, new_path = candidates[0], candidate_paths[0]  # The only pair sharing this key
            if not self._apply_relink(entry, new_path, cache):  # DB write failed
                continue

            logger.info(log_message, old_path=entry.path, new_path=new_path)
            relinked.append(entry)
            del self.new_paths[new_path]

        relinked_ids = {entry.id for entry in relinked}
        self.unlinked_entries = [
            entry for entry in self.unlinked_entries if entry.id not in relinked_ids
        ]
        self.relinked_entries.extend(relinked)

    def _merge_duplicate_path_entries(self, cache: dict[str, int]) -> None:
        """Merge any entry whose stored path collides with another entry's onto that entry.

        Entries here have already a full path + filename match.
        """
        duplicate_ids = set(self.library.duplicate_path_entry_ids or [])
        if not duplicate_ids:
            return

        merged: list[FileEntryTuple] = []
        for entry in self.unlinked_entries:
            if self.cancelled:
                break
            if entry.id in duplicate_ids and self._apply_relink(entry, entry.path, cache):
                merged.append(entry)

        merged_ids = {entry.id for entry in merged}
        self.unlinked_entries = [
            entry for entry in self.unlinked_entries if entry.id not in merged_ids
        ]
        self.relinked_entries.extend(merged)

    def _auto_relink_matched_entries(self, cache: dict[str, int]) -> None:
        """Attempt to automatically relink unlinked entries under available conditions.

        Auto-relink applies to:
            - Files with the same filename but different paths
                - Handles moves, moves + changes (Case #7)
            - Files with different names and/or paths but the same date_modified and file_size
                - Handles moves, renames + moves (Cases #3, #11)
            - Files with only a matching filename, as a last resort when nothing else matches
                - Handles moves + changes, and entries with no stored stats (Case #6)

        Auto-relink DOES NOT apply to:
            - Renames + Changes (Cases #2, #10)
            - Deletions (Case #1)
            - Ambiguous matches (Cases #4, #5, #8, #9, #12, #13)

        *(Cases are listed in the Library documentation)*
        """
        if not self.new_paths or not self.unlinked_entries:
            return

        def name_key(path: str) -> str:
            """Key of filename for relinking across path/stat changes."""
            return norm_str(
                posixpath.basename(path), case_sensitive=self.library.is_fs_case_sensitive
            )

        def stat_key(stat: StatTuple | None) -> tuple[float, int] | None:
            """Key of file stats for relinking across filename/path changes."""
            return None if stat is None else (stat.date_modified, stat.file_size)

        # Pass 1: Filename + metadata (Case #7)
        self._relink_unique_matches(
            cache,
            key_of_entry=lambda e: (name_key(e.path), stat_key(e.stat)),
            key_of_path=lambda p: (name_key(p), stat_key(self.new_paths[p])),
            log_message="[Sync] Automatically relinked moved file",
        )

        if self.cancelled:
            return

        # Pass 2: Different filename checking for same metadata (Cases #3, #11)
        self._relink_unique_matches(
            cache,
            key_of_entry=lambda e: stat_key(e.stat),
            key_of_path=lambda p: stat_key(self.new_paths[p]),
            log_message="[Sync] Automatically relinked renamed file (matched by size + mdate)",
        )

        if self.cancelled:
            return

        # Pass 3: Filename only, for anything that wasn't matched before
        # (Case #6, and entries with no stored stats)
        self._relink_unique_matches(
            cache,
            key_of_entry=lambda e: name_key(e.path),
            key_of_path=name_key,
            log_message="[Sync] Automatically relinked file by filename only",
        )

    def remove_unlinked_entries(self) -> None:
        """Remove unlinked entries from the Library."""
        # Path cache is updated in the library.
        self.library.remove_entries([entry.id for entry in self.unlinked_entries])
        self.unlinked_entries = []
