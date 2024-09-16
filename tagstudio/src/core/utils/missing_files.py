from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import structlog
from src.core.library import Entry, Library

IGNORE_ITEMS = [
    "$recycle.bin",
]

logger = structlog.get_logger()


@dataclass
class MissingRegistry:
    """State tracker for unlinked and moved files."""

    library: Library
    files_fixed_count: int = 0
    missing_files: list[Entry] = field(default_factory=list)

    @property
    def missing_files_count(self) -> int:
        return len(self.missing_files)

    def refresh_missing_files(self) -> Iterator[int]:
        """Track the number of Entries that point to an invalid file path."""
        logger.info("refresh_missing_files running")
        self.missing_files = []
        for i, entry in enumerate(self.library.get_entries()):
            full_path = self.library.library_dir / entry.path
            if not full_path.exists() or not full_path.is_file():
                self.missing_files.append(entry)
            yield i

    def match_missing_file(self, match_item: Entry) -> list[Path]:
        """Try to find missing entry files within the library directory.

        Works if files were just moved to different subfolders and don't have duplicate names.
        """
        matches = []
        for item in self.library.library_dir.glob(f"**/{match_item.path.name}"):
            if item.name == match_item.path.name:  # TODO - implement IGNORE_ITEMS
                new_path = Path(item).relative_to(self.library.library_dir)
                matches.append(new_path)

        return matches

    def fix_missing_files(self) -> Iterator[int]:
        """Attempt to fix missing files by finding a match in the library directory."""
        self.files_fixed_count = 0
        for i, entry in enumerate(self.missing_files, start=1):
            item_matches = self.match_missing_file(entry)
            if len(item_matches) == 1:
                logger.info("fix_missing_files", entry=entry, item_matches=item_matches)
                self.library.update_entry_path(entry.id, item_matches[0])
                self.files_fixed_count += 1
                # remove fixed file
                self.missing_files.remove(entry)
            yield i

    def execute_deletion(self) -> Iterator[int]:
        for i, missing in enumerate(self.missing_files, start=1):
            # TODO - optimize this by removing multiple entries at once
            self.library.remove_entries([missing.id])
            yield i

        self.missing_files = []
