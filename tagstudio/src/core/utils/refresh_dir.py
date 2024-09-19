from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from time import time

import structlog
from src.core import constants
from src.core.library import Entry, Library
from src.core.library.alchemy.models import Folder

logger = structlog.get_logger(__name__)


@dataclass
class RefreshDirTracker:
    library: Library
    dir_files_count: int = 0
    files_not_in_library: list[tuple[Folder, Path]] = field(default_factory=list)

    @property
    def files_count(self) -> int:
        return len(self.files_not_in_library)

    def save_new_files(self) -> Iterator[int]:
        """Save the list of files that are not in the library."""
        if not self.files_not_in_library:
            yield 0

        for idx, (folder, entry_path) in enumerate(self.files_not_in_library):
            self.library.add_entries(
                [
                    Entry(
                        path=entry_path,
                        folder=folder,
                        fields=self.library.default_fields,
                    )
                ]
            )
            yield idx

        self.files_not_in_library = []

    def refresh_dirs(self, folders: list[Folder]) -> Iterator[int]:
        """Scan a directory for changes.

        - Keep track of files which are not in library.
        - Remove files from library which are in ignored dirs.
        """
        if isinstance(folders, Folder):
            folders = [folders]

        start_time_total = time()

        self.files_not_in_library = []
        self.dir_files_count = 0

        for folder in folders:
            # yield values from self._refresh_dir
            yield from self._refresh_dir(folder)

        end_time_total = time()
        logger.info(
            "Directory scan time",
            duration=(end_time_total - start_time_total),
            new_files_count=self.dir_files_count,
        )

    def _refresh_dir(self, folder: Folder) -> Iterator[int]:
        start_time_loop = time()
        folder_path = folder.path
        for root, _, files in folder_path.walk():
            if "$RECYCLE.BIN" in str(root).upper():
                continue

            # - if directory contains file `.ts_noindex` then skip the directory
            if constants.TS_FOLDER_NOINDEX in files:
                logger.info("TS Ignore File found, skipping", directory=root)
                # however check if the ignored files aren't in the library; if so, remove them
                entries_to_remove = []
                for file in files:
                    file_path = root / file
                    entry_path = file_path.relative_to(folder_path)
                    if entry := self.library.get_path_entry(entry_path):
                        entries_to_remove.append(entry.id)

                    # Yield output every 1/30 of a second
                    if (time() - start_time_loop) > 0.034:
                        # yield but dont increase the count
                        yield self.dir_files_count
                        start_time_loop = time()

                self.library.remove_entries(entries_to_remove)
                continue

            for file in files:
                path = root / file
                self.dir_files_count += 1

                relative_path = path.relative_to(folder_path)
                # TODO - load these in batch somehow
                if not self.library.get_path_entry(relative_path):
                    self.files_not_in_library.append((folder, relative_path))

                # Yield output every 1/30 of a second
                if (time() - start_time_loop) > 0.034:
                    yield self.dir_files_count
                    start_time_loop = time()
