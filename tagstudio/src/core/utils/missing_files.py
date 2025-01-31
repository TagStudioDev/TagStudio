from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import structlog
from src.core.library import Entry, Library
from src.core.utils.refresh_dir import GLOBAL_IGNORE_SET

logger = structlog.get_logger()


@dataclass
class MissingRegistry:
    """State tracker for unlinked and moved files."""

    library: Library
    files_fixed_count: int = 0
    missing_file_entries: list[Entry] = field(default_factory=list)

    @property
    def missing_file_entries_count(self) -> int:
        return len(self.missing_file_entries)

    def refresh_missing_files(self) -> Iterator[int]:
        """Track the number of entries that point to an invalid filepath."""
        logger.info("[refresh_missing_files] Refreshing missing files...")
        self.missing_file_entries = []
        for i, entry in enumerate(self.library.get_entries()):
            full_path = self.library.library_dir / entry.path
            if not full_path.exists() or not full_path.is_file():
                self.missing_file_entries.append(entry)
            yield i

    def match_missing_file_entry(self, match_entry: Entry) -> list[Path]:
        """Try and match unlinked file entries with matching results in the library directory.

        Works if files were just moved to different subfolders and don't have duplicate names.
        """
        matches = []
        for path in self.library.library_dir.glob(f"**/{match_entry.path.name}"):
            # Ensure matched file isn't in a globally ignored folder
            skip: bool = False
            for part in path.parts:
                if part in GLOBAL_IGNORE_SET:
                    skip = True
                    break
            if skip:
                continue
            if path.name == match_entry.path.name:
                new_path = Path(path).relative_to(self.library.library_dir)
                matches.append(new_path)

        logger.info("[MissingRegistry] Matches", matches=matches)
        return matches

    def fix_unlinked_entries(self) -> Iterator[int]:
        """Attempt to fix unlinked file entries by finding a match in the library directory."""
        self.files_fixed_count = 0
        matched_entries: list[Entry] = []
        for i, entry in enumerate(self.missing_file_entries):
            item_matches = self.match_missing_file_entry(entry)
            if len(item_matches) == 1:
                logger.info(
                    "[fix_unlinked_entries]",
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
                matched_entries.append(entry)
            yield i

        for entry in matched_entries:
            self.missing_file_entries.remove(entry)

    def execute_deletion(self) -> None:
        self.library.remove_entries(
            list(map(lambda missing: missing.id, self.missing_file_entries))
        )

        self.missing_file_entries = []
