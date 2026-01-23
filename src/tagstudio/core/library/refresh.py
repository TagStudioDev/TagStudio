# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import shutil
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime as dt
from pathlib import Path
from time import time

import structlog
from wcmatch import glob

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.ignore import PATH_GLOB_FLAGS, Ignore, ignore_to_glob
from tagstudio.core.utils.silent_subprocess import silent_run  # pyright: ignore
from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger(__name__)


@dataclass
class RefreshTracker:
    library: Library

    _paths_to_id: dict[Path, int] = field(default_factory=dict)
    _expected_paths: set[Path] = field(default_factory=set)

    _missing_paths: dict[Path, int] = field(default_factory=dict)
    _new_paths: set[Path] = field(default_factory=set)

    @property
    def missing_files_count(self) -> int:
        return len(self._missing_paths)

    @property
    def new_files_count(self) -> int:
        return len(self._new_paths)

    def _add_path(self, entry_id: int, path: Path):
        self._paths_to_id[path] = entry_id
        self._expected_paths.add(path)

    def _del_path(self, path: Path):
        self._paths_to_id.pop(path)
        self._expected_paths.remove(path)

    def save_new_files(self) -> Iterator[int]:
        """Save the list of files that are not in the library."""
        batch_size = 200

        all_entries = [
            Entry(
                path=entry_path,
                folder=unwrap(self.library.folder),
                fields=[],
                date_added=dt.now(),
            )
            for entry_path in self._new_paths
        ]
        for start in range(0, len(all_entries), batch_size):
            yield start
            end = start + batch_size
            entries = all_entries[start:end]
            entry_ids = self.library.add_entries(entries)

            assert len(entry_ids) == len(entries)
            for i in range(len(entry_ids)):
                id = entry_ids[i]
                path = entries[i].path
                self._add_path(id, path)

        self._new_paths.clear()

    def fix_unlinked_entries(self):
        """Attempt to fix unlinked file entries by finding a match in the library directory."""
        new_paths: dict[Path, list[Path]] = {}
        for path in self._new_paths:
            name = path.relative_to(path.parent)
            new_paths.setdefault(name, []).append(path)

        fixed: list[tuple[int, Path, Path]] = []
        for (
            path,
            entry_id,
        ) in self._missing_paths.items():
            name = Path(path.name)
            if name not in new_paths or len(new_paths[name]) != 1:
                continue
            new_path = new_paths.pop(name)[0]
            self._new_paths.remove(new_path)

            fixed.append((entry_id, path, new_path))

        paths = ((id, new_path) for (id, _path, new_path) in fixed)
        if not self.library.update_entry_paths(paths):
            return

        for entry_id, path, new_path in fixed:
            self._del_path(path)
            self._add_path(entry_id, new_path)
            self._missing_paths.pop(path)

    def remove_unlinked_entries(self) -> None:
        to_remove = []
        for path, id in self._missing_paths.items():
            to_remove.append(id)
            self._del_path(path)
        self._missing_paths.clear()

        self.library.remove_entries(to_remove)

    def refresh_dir(self, library_dir: Path, force_internal_tools: bool = False) -> Iterator[int]:
        """Scan a directory for files, and add those relative filenames to internal variables.

        Args:
            library_dir (Path): The library directory.
            force_internal_tools (bool): Option to force the use of internal tools for scanning
                (i.e. wcmatch) instead of using tools found on the system (i.e. ripgrep).
        """
        if self.library.library_dir is None:
            raise ValueError("No library directory set.")

        start_time = time()
        self._paths_to_id = dict((p, i) for i, p in self.library.all_paths())
        self._expected_paths = set(self._paths_to_id.keys())
        logger.info(
            "[Refresh]: Fetch entry paths",
            duration=(time() - start_time),
        )

        ignore_patterns = Ignore.get_patterns(library_dir)

        yield 0
        progress = None
        if not force_internal_tools:
            progress = self.__rg(library_dir, ignore_patterns)

        # Use ripgrep if it was found and working, else fallback to wcmatch.
        if progress is None:
            progress = self.__wc(library_dir, ignore_patterns)
        yield from progress

    def __rg(self, library_dir: Path, ignore_patterns: list[str]) -> Iterator[int] | None:
        """Use ripgrep to return a list of matched directories and files.

        Return `None` if ripgrep not found on system.
        """
        rg_path = shutil.which("rg")
        # Use ripgrep if found on system
        if rg_path is not None:
            logger.info("[Refresh: Using ripgrep for scanning]")

            compiled_ignore_path = library_dir / ".TagStudio" / ".compiled_ignore"

            # Write compiled ignore patterns (built-in + user) to a temp file to pass to ripgrep
            with open(compiled_ignore_path, "w") as pattern_file:
                pattern_file.write("\n".join(ignore_patterns))

            start_time = time()
            result = silent_run(
                " ".join(
                    [
                        "rg",
                        "--files",
                        "--follow",
                        "--hidden",
                        "--ignore-file",
                        f'"{str(compiled_ignore_path)}"',
                    ]
                ),
                cwd=library_dir,
                capture_output=True,
                shell=True,
            )
            logger.info(
                "[Refresh]: ripgrep scan time",
                duration=(time() - start_time),
            )
            compiled_ignore_path.unlink()

            if result.stderr:
                logger.error(result.stderr)

            paths = set(Path(p) for p in result.stdout.decode("utf-8").splitlines())
            self.__add(library_dir, paths)
            yield len(paths)
            return None

        logger.warning("[Refresh: ripgrep not found on system]")
        return None

    def __wc(self, library_dir: Path, ignore_patterns: list[str]) -> Iterator[int]:
        logger.info("[Refresh]: Falling back to wcmatch for scanning")

        ignore_patterns = ignore_to_glob(ignore_patterns)
        try:
            paths: set[Path] = set()

            start_time = time()
            search = glob.iglob(
                "***/*", root_dir=library_dir, flags=PATH_GLOB_FLAGS, exclude=ignore_patterns
            )
            for i, path in enumerate(search):
                if i < 100 or (i % 100) == 0:
                    yield i
                paths.add(Path(path))
            logger.info(
                "[Refresh]: wcmatch scan time",
                duration=(time() - start_time),
            )
            yield len(paths)

            self.__add(library_dir, paths)
        except ValueError:
            logger.info("[Refresh]: ValueError when refreshing directory with wcmatch!")

    def __add(self, library_dir: Path, paths: set[Path]):
        start_time_total = time()

        self._new_paths = paths.difference(self._expected_paths)

        missing = self._expected_paths.difference(paths)
        self._missing_paths = dict((p, self._paths_to_id[p]) for p in missing)

        end_time_total = time()
        logger.info(
            "[Refresh]: Directory scan time",
            path=library_dir,
            duration=(end_time_total - start_time_total),
            files_scanned=len(paths),
            missing=len(self._missing_paths),
            new=len(self._new_paths),
        )
