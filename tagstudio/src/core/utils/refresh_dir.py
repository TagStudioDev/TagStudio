from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from time import time

import structlog
from src.core.constants import TS_FOLDER_NAME
from src.core.library import Entry, Library

logger = structlog.get_logger(__name__)

GLOBAL_IGNORE_SET: set[str] = set(
    [
        TS_FOLDER_NAME,
        "$RECYCLE.BIN",
        ".Trashes",
        ".Trash",
        "tagstudio_thumbs",
        ".fseventsd",
        ".Spotlight-V100",
        "System Volume Information",
        ".DS_Store",
    ]
)


@dataclass
class RefreshDirTracker:
    library: Library
    files_not_in_library: list[Path] = field(default_factory=list)

    @property
    def files_count(self) -> int:
        return len(self.files_not_in_library)

    def save_new_files(self):
        """Save the list of files that are not in the library."""
        if self.files_not_in_library:
            entries = [
                Entry(
                    path=entry_path,
                    folder=self.library.folder,
                    fields=[],
                )
                for entry_path in self.files_not_in_library
            ]
            self.library.add_entries(entries)

        self.files_not_in_library = []

        yield

    def refresh_dir(self, lib_path: Path) -> Iterator[int]:
        """Scan a directory for files, and add those relative filenames to internal variables."""
        if self.library.library_dir is None:
            raise ValueError("No library directory set.")

        start_time_total = time()
        start_time_loop = time()

        self.files_not_in_library = []
        dir_file_count = 0

        for f in lib_path.glob("**/*"):
            end_time_loop = time()
            # Yield output every 1/30 of a second
            if (end_time_loop - start_time_loop) > 0.034:
                yield dir_file_count
                start_time_loop = time()

            # Skip if the file/path is already mapped in the Library
            if f in self.library.included_files:
                dir_file_count += 1
                continue

            # Ignore if the file is a directory
            if f.is_dir():
                continue

            # Ensure new file isn't in a globally ignored folder
            skip: bool = False
            for part in f.parts:
                # NOTE: Files starting with "._" are sometimes generated by macOS Finder.
                # More info: https://lists.apple.com/archives/applescript-users/2006/Jun/msg00180.html
                if part.startswith("._") or part in GLOBAL_IGNORE_SET:
                    skip = True
                    break
            if skip:
                continue

            dir_file_count += 1
            self.library.included_files.add(f)

            relative_path = f.relative_to(lib_path)
            # TODO - load these in batch somehow
            if not self.library.has_path_entry(relative_path):
                self.files_not_in_library.append(relative_path)

        end_time_total = time()
        yield dir_file_count
        logger.info(
            "Directory scan time",
            path=lib_path,
            duration=(end_time_total - start_time_total),
            files_not_in_lib=self.files_not_in_library,
            files_scanned=dir_file_count,
        )
