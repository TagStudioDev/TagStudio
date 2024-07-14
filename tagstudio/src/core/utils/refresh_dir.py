import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from src.core.constants import TS_FOLDER_NAME
from src.core.library import Library, Entry


@dataclass
class RefreshDirTracker:
    library: Library
    dir_file_count: int = 0
    files_not_in_library: list[Path] = field(default_factory=list)

    @property
    def files_count(self) -> int:
        return len(self.files_not_in_library)

    def save_new_files(self) -> Iterator[int]:
        """Save the list of files that are not in the library."""
        if not self.files_not_in_library:
            yield 0

        for idx, entry_path in enumerate(self.files_not_in_library):
            self.library.add_entries([Entry(path=entry_path)])
            yield idx

        self.files_not_in_library = []

    def refresh_dir(self) -> Iterator[int]:
        """Scan a directory for files, and add those relative filenames to internal variables."""
        if self.library.library_dir is None:
            raise ValueError("No library path set.")

        start_time = time.time()
        self.files_not_in_library = []
        self.dir_file_count = 0

        for path in self.library.library_dir.glob("**/*"):
            str_path = str(path)
            if (
                path.is_dir()
                or "$RECYCLE.BIN" in str_path
                or TS_FOLDER_NAME in str_path
                or "tagstudio_thumbs" in str_path
            ):
                continue

            suffix = path.suffix.lower().lstrip(".")
            if suffix in self.library.ignored_extensions:
                continue

            self.dir_file_count += 1
            relative_path = path.relative_to(self.library.library_dir)
            # TODO - load these in batch somehow
            if not self.library.has_path_entry(relative_path):
                self.files_not_in_library.append(relative_path)

            end_time = time.time()
            # Yield output every 1/30 of a second
            if (end_time - start_time) > 0.034:
                yield self.dir_file_count
