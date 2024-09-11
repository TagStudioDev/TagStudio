from time import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from src.core.constants import TS_FOLDER_NAME, LibraryPrefs
from src.core.library import Library, Entry

logger = structlog.get_logger(__name__)


@dataclass
class RefreshDirTracker:
    library: Library
    files_not_in_library: list[Path] = field(default_factory=list)

    @property
    def files_count(self) -> int:
        return len(self.files_not_in_library)

    def save_new_files(self) -> Iterator[int]:
        """Save the list of files that are not in the library."""
        if not self.files_not_in_library:
            yield 0

        for idx, entry_path in enumerate(self.files_not_in_library):
            self.library.add_entries(
                [
                    Entry(
                        path=entry_path,
                        folder=self.library.folder,
                        fields=self.library.default_fields,
                    )
                ]
            )
            yield idx

        self.files_not_in_library = []

    def refresh_dir(self, lib_path: Path) -> Iterator[int]:
        """Scan a directory for files, and add those relative filenames to internal variables."""
        if self.library.library_dir is None:
            raise ValueError("No library directory set.")

        is_exclude_list = self.library.prefs(LibraryPrefs.IS_EXCLUDE_LIST)
        exclude_list = set(self.library.prefs(LibraryPrefs.EXTENSION_LIST))

        def skip_suffix(suffix: str) -> bool:
            """Determine if the file extension should be skipped.

            Declared as local function as it's faster.

            - check if the suffix is in the library's "exclude list"
            - if library uses "exclude mode", and extensions is in the list, we skip
            - if library uses "include mode", and extensions is not in the list, we skip
            """
            return (suffix.lower() in exclude_list) == is_exclude_list

        start_time_total = time()
        start_time_loop = time()

        self.files_not_in_library = []
        dir_file_count = 0

        for path_item in lib_path.glob("**/*"):
            str_path = str(path_item)
            if path_item.is_dir():
                continue

            if "$RECYCLE.BIN" in str_path or TS_FOLDER_NAME in str_path:
                continue

            if skip_suffix(path_item.suffix):
                continue

            dir_file_count += 1
            relative_path = path_item.relative_to(lib_path)
            # TODO - load these in batch somehow
            if not self.library.has_path_entry(relative_path):
                self.files_not_in_library.append(relative_path)

            # Yield output every 1/30 of a second
            if (time() - start_time_loop) > 0.034:
                yield dir_file_count
                start_time_loop = time()

        end_time_total = time()
        logger.info(
            "Directory scan time",
            path=lib_path,
            duration=(end_time_total - start_time_total),
            new_files_count=dir_file_count,
        )
