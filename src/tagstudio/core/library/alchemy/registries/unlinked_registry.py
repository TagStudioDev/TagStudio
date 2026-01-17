from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import structlog
from wcmatch import pathlib

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.ignore import PATH_GLOB_FLAGS, Ignore, ignore_to_glob
from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger()


@dataclass
class UnlinkedRegistry:
    """State tracker for unlinked entries."""

    lib: Library
    files_fixed_count: int = 0
    unlinked_entries: list[Entry] = field(default_factory=list)

    @property
    def unlinked_entries_count(self) -> int:
        return len(self.unlinked_entries)

    def reset(self):
        self.unlinked_entries.clear()

    def refresh_unlinked_files(self) -> Iterator[int]:
        """Track the number of entries that point to an invalid filepath."""
        logger.info("[UnlinkedRegistry] Refreshing unlinked files...")

        self.unlinked_entries = []
        for i, entry in enumerate(self.lib.all_entries()):
            full_path = unwrap(self.lib.library_dir) / entry.path
            if not full_path.exists() or not full_path.is_file():
                self.unlinked_entries.append(entry)
            yield i

    def match_unlinked_file_entry(self, match_entry: Entry) -> list[Path]:
        """Try and match unlinked file entries with matching results in the library directory.

        Works if files were just moved to different subfolders and don't have duplicate names.
        """
        library_dir = unwrap(self.lib.library_dir)
        matches: list[Path] = []

        # NOTE: ignore_to_glob() is needed for wcmatch, not ripgrep.
        ignore_patterns = ignore_to_glob(Ignore.get_patterns(library_dir))
        for path in pathlib.Path(str(library_dir)).glob(
            f"***/{match_entry.path.name}",
            flags=PATH_GLOB_FLAGS,
            exclude=ignore_patterns,
        ):
            if path.is_dir():
                continue
            if path.name == match_entry.path.name:
                new_path = Path(path).relative_to(library_dir)
                matches.append(new_path)

        logger.info("[UnlinkedRegistry] Matches", matches=matches)
        return matches

    def fix_unlinked_entries(self) -> Iterator[int]:
        """Attempt to fix unlinked file entries by finding a match in the library directory."""
        self.files_fixed_count = 0
        matched_entries: list[Entry] = []
        for i, entry in enumerate(self.unlinked_entries):
            yield i
            item_matches = self.match_unlinked_file_entry(entry)
            if len(item_matches) == 1:
                logger.info(
                    "[UnlinkedRegistry]",
                    entry=entry.path.as_posix(),
                    item_matches=item_matches[0].as_posix(),
                )
                if not self.lib.update_entry_path(entry.id, item_matches[0]):
                    try:
                        match = unwrap(self.lib.get_entry_full_by_path(item_matches[0]))
                        entry_full = unwrap(self.lib.get_entry_full(entry.id))
                        self.lib.merge_entries(entry_full, match)
                    except AttributeError:
                        continue
                self.files_fixed_count += 1
                matched_entries.append(entry)

        for entry in matched_entries:
            self.unlinked_entries.remove(entry)

    def remove_unlinked_entries(self) -> None:
        self.lib.remove_entries(list(map(lambda unlinked: unlinked.id, self.unlinked_entries)))
        self.unlinked_entries = []
