# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime as dt
from pathlib import Path
from time import time

import structlog
from wcmatch import glob, pathlib

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.ignore import PATH_GLOB_FLAGS, Ignore, ignore_to_glob
from tagstudio.core.library.scanners import scan_paths
from tagstudio.core.utils.filesystem import is_fs_case_sensitive
from tagstudio.core.utils.normalization import norm_path
from tagstudio.core.utils.stat import get_date_created, get_date_modified, get_file_size
from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger(__name__)

# Yield progress this often during a loop to avoid overwhelming the UI.
# TODO: Look into whether or not this can be handled on the UI side.
YIELD_INTERVAL_SECONDS = 0.034


@dataclass
class LibrarySyncEngine:
    """Keeps a Library's entries in sync with its content directories on disk."""

    library: Library
    new_paths: list[Path] = field(default_factory=list)
    paths_to_restat: list[tuple[int, Path]] = field(default_factory=list)
    unlinked_entries: list[Entry] = field(default_factory=list)
    relinked_entries: list[Entry] = field(default_factory=list)
    manual_relink_count: int = 0
    cancelled: bool = False

    _scanned_paths: list[Path] = field(default_factory=list, init=False, repr=False)
    _filename_to_path_map: dict[Path, list[Path]] | None = field(
        default=None, init=False, repr=False
    )

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
        self.new_paths = []
        self.paths_to_restat = []
        self.unlinked_entries = []
        self.relinked_entries = []
        self._scanned_paths = []
        self._filename_to_path_map = None

    def _get_case_sensitivity(self) -> bool:
        if self.library.is_case_sensitive_fs is None:
            self.library.is_case_sensitive_fs = is_fs_case_sensitive()
        return self.library.is_case_sensitive_fs

    def sync_dir(
        self, library_dir: Path, force_internal_scanner: bool = False
    ) -> Iterator[tuple[int, int]]:
        """Scan library directory for files, then reconcile them against the Library's entries.

        - Entries with no matching file on disk are marked as "unlinked"
            - Automatically relink to appropriate new files on disk where possible
        - Remaining new files on disk are added as new entires
        - Remaining unlinked entries are tracked for manual review.

        Yields (searched_count, found_count)

        Args:
            library_dir (Path): The library directory.
            force_internal_scanner (bool): Option to force the use of the internal scanner
                (i.e. wcmatch) instead of third-party tools found on the system (i.e. ripgrep).
        """
        self.reset()
        self.cancelled = False

        case_sensitive = self._get_case_sensitivity()
        cache = self.library.get_or_build_path_cache()
        unvisited = set(cache.keys())
        ignore_patterns = Ignore.get_patterns(library_dir)

        start_time = time()
        start_time_loop = time()
        count = 0
        for raw_path in scan_paths(library_dir, ignore_patterns, force_internal_scanner):
            if self.cancelled:
                break
            count += 1
            self._scanned_paths.append(raw_path)
            key = norm_path(raw_path, case_sensitive=case_sensitive)
            entry_id = cache.get(key)
            if entry_id is not None:
                unvisited.discard(key)
                self.paths_to_restat.append((entry_id, raw_path))
            else:
                self.new_paths.append(raw_path)

            if (time() - start_time_loop) > YIELD_INTERVAL_SECONDS:
                yield count, len(self.new_paths)
                start_time_loop = time()

        if self.cancelled:
            yield count, len(self.new_paths)
            logger.info("[Sync] Directory scan cancelled", path=library_dir, files_scanned=count)
            return

        unlinked_ids = {cache[key] for key in unvisited}
        if self.library.duplicate_path_entry_ids:
            unlinked_ids.update(self.library.duplicate_path_entry_ids)
        if unlinked_ids:
            self.unlinked_entries = self.library.get_entries(list(unlinked_ids))

        self._auto_relink_matched_entries(case_sensitive, cache)

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
        batch_size = 200
        library_dir = unwrap(self.library.library_dir)

        index = 0
        while index < len(self.new_paths):
            if self.cancelled:
                break
            yield index
            end = min(len(self.new_paths), index + batch_size)
            batch = self.new_paths[index:end]
            entries = []
            for entry_path in batch:
                file_stat = (library_dir / entry_path).stat()
                entries.append(
                    Entry(
                        path=entry_path,
                        fields=[],
                        date_created=get_date_created(file_stat),
                        date_modified=get_date_modified(file_stat),
                        file_size=get_file_size(file_stat),
                        date_added=dt.now(),
                    )
                )
            self.library.add_entries(entries)  # Path cache is updated in the library
            index = end
        self.new_paths = self.new_paths[index:]  # Saved entries are removed from new_paths

    def sync_entry_stats(self) -> Iterator[int]:
        """Refresh cached os.stat() metadata for entries already known to the Library."""
        batch_size = 500

        index = 0
        while index < len(self.paths_to_restat):
            if self.cancelled:
                break
            yield index
            end = min(len(self.paths_to_restat), index + batch_size)
            self.library.refresh_entries_stats(self.paths_to_restat[index:end])
            index = end
        self.paths_to_restat = self.paths_to_restat[index:]

    def _build_filename_to_path_map(self, case_sensitive: bool) -> dict[Path, list[Path]]:
        index: dict[Path, list[Path]] = {}
        for path in self._scanned_paths:
            key = norm_path(Path(path.name), case_sensitive=case_sensitive)
            index.setdefault(key, []).append(path)
        return index

    def _glob_for_filename(self, filename: str, case_sensitive: bool) -> list[Path]:
        """Search the library directory for files matching `filename`.

        Used only as a fallback when find_relink_candidates() is called without a prior
        sync_dir() scan in this engine instance to reuse results from.
        """
        library_dir = unwrap(self.library.library_dir)
        ignore_patterns = ignore_to_glob(Ignore.get_patterns(library_dir))
        target_path = norm_path(Path(filename), case_sensitive=case_sensitive)
        flags = PATH_GLOB_FLAGS | (0 if case_sensitive else glob.IGNORECASE)

        matches: list[Path] = []
        for path in pathlib.Path(str(library_dir)).glob(
            patterns=f"***/{glob.escape(filename)}",
            flags=flags,
            exclude=ignore_patterns,
        ):
            if path.is_dir():
                continue
            candidate = Path(path).relative_to(library_dir)
            if norm_path(Path(candidate.name), case_sensitive=case_sensitive) == target_path:
                matches.append(candidate)
        return matches

    def find_relink_candidates(self, entry: Entry) -> list[Path]:
        """Try to find files in the library directory matching an unlinked entry's filename.

        Comparisons are made using NFD normalization and the assumed filesystem's case sensitivity.
        """
        case_sensitive = self._get_case_sensitivity()
        target_key = norm_path(Path(entry.path.name), case_sensitive=case_sensitive)

        if self._scanned_paths:
            if self._filename_to_path_map is None:
                self._filename_to_path_map = self._build_filename_to_path_map(case_sensitive)
            matches = list(self._filename_to_path_map.get(target_key, []))
        else:
            matches = self._glob_for_filename(entry.path.name, case_sensitive)

        logger.info("[Sync] Relink candidates", entry=entry.path.as_posix(), matches=matches)
        return matches

    def _apply_relink(
        self, entry: Entry, new_path: Path, cache: dict[Path, int], case_sensitive: bool
    ) -> bool:
        """Assign `new_path` to the `entry`, merging into a single entry if entries exist for both.

        Returns:
            bool: True if the relink was successful.
        """
        new_key = norm_path(new_path, case_sensitive=case_sensitive)

        existing_id = cache.get(new_key)
        if existing_id is not None and existing_id != entry.id:
            # Merge both entries into one with the single path
            target = unwrap(self.library.get_entry_full(existing_id))
            source = unwrap(self.library.get_entry_full(entry.id))
            return self.library.merge_entries(source, target)
        return self.library.update_entry_path(entry.id, new_path)

    def relink_unlinked_entries(self) -> Iterator[int]:
        """Attempt to fix unlinked entries by finding a single matching file in the library."""
        self.manual_relink_count = 0
        case_sensitive = self._get_case_sensitivity()
        cache = self.library.get_or_build_path_cache()
        matched: list[Entry] = []

        for i, entry in enumerate(self.unlinked_entries):
            yield i
            candidates = self.find_relink_candidates(entry)
            if len(candidates) != 1:
                continue
            new_path = candidates[0]
            if not self._apply_relink(entry, new_path, cache, case_sensitive):
                continue

            self.manual_relink_count += 1
            matched.append(entry)
            logger.info(
                "[Sync] Relinked entry",
                entry=entry.path.as_posix(),
                new_path=new_path.as_posix(),
            )

        for entry in matched:
            self.unlinked_entries.remove(entry)

    def _auto_relink_matched_entries(self, case_sensitive: bool, cache: dict[Path, int]) -> None:
        """Attempt to automatically relink unlinked entries under available conditions.

        Auto-relink applies to:
            - Files with the same filename but different paths
                - Handles moves, moves + changes
            - Files with different names and/or paths but the same date_modified and file_size
                - Handles moves, renames + moves

        Auto-relink DOES NOT apply to:
            - Renames + Moves + Changes
            - Deletions
            - Ambiguous (more than one) matches
        """
        if not self.new_paths or not self.unlinked_entries:
            return

        library_dir = unwrap(self.library.library_dir)

        # Pass 1: Filename + metadata
        by_name_and_stat: dict[tuple[Path, float | None, int | None], list[Entry]] = {}
        for entry in self.unlinked_entries:
            name_key = norm_path(Path(entry.path.name), case_sensitive=case_sensitive)
            by_name_and_stat.setdefault(
                (name_key, entry.date_modified, entry.file_size), []
            ).append(entry)

        relinked: list[Entry] = []
        remaining_new: list[Path] = []
        stats_by_path: dict[Path, tuple[float | None, int | None]] = {}

        for new_path in self.new_paths:
            try:
                file_stat = (library_dir / new_path).stat()
            except OSError as e:
                logger.error(
                    "[Sync] Could not stat file during auto-relink check",
                    path=new_path,
                    error=e,
                )
                remaining_new.append(new_path)
                continue

            mtime = get_date_modified(file_stat)
            size = get_file_size(file_stat)
            stats_by_path[new_path] = (mtime, size)

            name_key = norm_path(Path(new_path.name), case_sensitive=case_sensitive)
            key = (name_key, mtime, size)
            candidates = by_name_and_stat.get(key, [])
            if len(candidates) != 1:
                remaining_new.append(new_path)
                continue

            entry = candidates[0]
            if not self._apply_relink(entry, new_path, cache, case_sensitive):
                remaining_new.append(new_path)
                continue
            by_name_and_stat[key] = []  # Don't match a second new_path here

            logger.info(
                "[Sync] Automatically relinked moved file",
                old_path=entry.path.as_posix(),
                new_path=new_path.as_posix(),
            )
            relinked.append(entry)

        for entry in relinked:
            self.unlinked_entries.remove(entry)

        # Pass 2: Different filename checking for same metadata
        by_stat_only: dict[tuple[float | None, int | None], list[Entry]] = {}
        for entry in self.unlinked_entries:
            by_stat_only.setdefault((entry.date_modified, entry.file_size), []).append(entry)

        still_remaining: list[Path] = []
        for new_path in remaining_new:
            stat_key = stats_by_path.get(new_path)
            if stat_key is None:
                still_remaining.append(new_path)
                continue

            candidates = by_stat_only.get(stat_key, [])
            if len(candidates) != 1:
                still_remaining.append(new_path)
                continue

            entry = candidates[0]
            if not self._apply_relink(entry, new_path, cache, case_sensitive):
                still_remaining.append(new_path)
                continue
            by_stat_only[stat_key] = []

            logger.info(
                "[Sync] Automatically relinked renamed file (matched by size/date only)",
                old_path=entry.path.as_posix(),
                new_path=new_path.as_posix(),
            )
            relinked.append(entry)
            self.unlinked_entries.remove(entry)

        self.new_paths = still_remaining
        self.relinked_entries = relinked

    def remove_unlinked_entries(self) -> None:
        """Remove unlinked entries from the Library."""
        # Path cache is updated in the library.
        self.library.remove_entries([entry.id for entry in self.unlinked_entries])
        self.unlinked_entries = []
