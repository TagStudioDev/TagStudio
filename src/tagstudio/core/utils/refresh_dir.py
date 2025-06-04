from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime as dt
from pathlib import Path
from time import time

import structlog
from wcmatch import pathlib

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.ignore import PATH_GLOB_FLAGS, Ignore

logger = structlog.get_logger(__name__)


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
                    folder=self.library.folder,  # pyright: ignore[reportArgumentType]
                    fields=[],
                    date_added=dt.now(),
                )
                for entry_path in self.files_not_in_library
            ]
            self.library.add_entries(entries)

        self.files_not_in_library = []

        yield

    def refresh_dir(self, library_dir: Path) -> Iterator[int]:
        """Scan a directory for files, and add those relative filenames to internal variables."""
        if self.library.library_dir is None:
            raise ValueError("No library directory set.")

        start_time_total = time()
        start_time_loop = time()

        self.files_not_in_library = []
        dir_file_count = 0

        ignore_patterns = Ignore.get_patterns(library_dir)
        logger.info(ignore_patterns)
        for f in pathlib.Path(str(library_dir)).glob(
            "***/*", flags=PATH_GLOB_FLAGS, exclude=ignore_patterns
        ):
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

            dir_file_count += 1
            self.library.included_files.add(f)

            relative_path = f.relative_to(library_dir)
            # TODO - load these in batch somehow
            if not self.library.has_path_entry(relative_path):
                self.files_not_in_library.append(relative_path)

        end_time_total = time()
        yield dir_file_count
        logger.info(
            "Directory scan time",
            path=library_dir,
            duration=(end_time_total - start_time_total),
            files_scanned=dir_file_count,
            ignore_patterns=ignore_patterns,
        )
