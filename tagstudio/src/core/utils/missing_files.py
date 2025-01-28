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

        logger.info("Matches", matches=matches)
        return matches

    def fix_missing_files(self) -> Iterator[int]:
        """Attempt to fix missing files by finding a match in the library directory."""
        self.files_fixed_count = 0
        files_to_remove = []
        logger.error(self.missing_files)
        for i, entry in enumerate(self.missing_files):
            logger.error(entry.path)
            item_matches = self.match_missing_file(entry)
            if len(item_matches) == 1:
                logger.info(
                    "fix_missing_files",
                    entry=entry.path.as_posix(),
                    item_matches=item_matches[0].as_posix(),
                )
                if not self.library.update_entry_path(entry.id, item_matches[0]):
                    try:
                        match = self.library.get_entry_full_by_path(item_matches[0])
                        entry_full = self.library.get_entry_full(entry.id)
                        self.library.merge_entries(entry_full, match)
                    except AttributeError:
                        continue
                self.files_fixed_count += 1
                files_to_remove.append(entry)
            yield i

        for entry in files_to_remove:
            self.missing_files.remove(entry)

    def execute_deletion(self) -> None:
        self.library.remove_entries(list(map(lambda missing: missing.id, self.missing_files)))

        self.missing_files = []
