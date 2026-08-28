# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import shutil
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime as dt
from pathlib import Path
from time import time

import structlog
from wcmatch import pathlib

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.ignore import PATH_GLOB_FLAGS, Ignore, ignore_to_glob

logger = structlog.get_logger(__name__)


@dataclass
class RefreshTracker:
    library: Library
    files_not_in_library: list[Path] = field(default_factory=list)

    @property
    def files_count(self) -> int:
        return len(self.files_not_in_library)

    def save_new_files(self) -> Iterator[int]:
        """Save the list of files that are not in the library."""
        batch_size = 200

        index = 0
        while index < len(self.files_not_in_library):
            yield index
            end = min(len(self.files_not_in_library), index + batch_size)
            entries = [
                Entry(
                    path=entry_path,
                    fields=[],
                    date_added=dt.now(),
                )
                for entry_path in self.files_not_in_library[index:end]
            ]
            self.library.add_entries(entries)
            index = end
        self.files_not_in_library = []

    def refresh_dir(self, force_internal_tools: bool = False) -> Iterator[int]:
        """Scan a directory for files, and add those relative filenames to internal variables.

        Args:
            force_internal_tools (bool): Option to force the use of internal tools for scanning
                (i.e. wcmatch) instead of using tools found on the system (i.e. ripgrep).
        """
        if self.library.library_dir is None:
            raise ValueError("No library directory set.")

        scanning_time_start = time()
        yield_output_loop_start = time()
        total_files_discovered: int = 0

        known_paths = {Path(path) for path in self.library.get_paths()}
        self.files_not_in_library = []

        for path in scan_for_files(self.library.library_dir, force_internal_tools):
            # Yield output every 1/30 of a second
            yield_output_loop_end = time()

            if (yield_output_loop_end - yield_output_loop_start) > 0.034:
                yield total_files_discovered
                yield_output_loop_start = time()

            # Ignore if the file is a directory
            if path.is_dir():
                continue

            total_files_discovered += 1
            relative_path = path.relative_to(self.library.library_dir)

            if relative_path not in known_paths:
                self.files_not_in_library.append(relative_path)

        scanning_time_end = time()
        yield total_files_discovered

        logger.info(
            "[Refresh] Scan completed",
            scan_dir=self.library.library_dir,
            duration=(scanning_time_end - scanning_time_start),
            files_scanned=total_files_discovered,
        )


def scan_for_files(scan_dir: Path, force_internal_tools: bool) -> Iterator[Path]:
    ignore_patterns = Ignore.get_patterns(scan_dir)

    ripgrep_path = shutil.which("rg")

    if ripgrep_path is None or force_internal_tools:
        yield from _scan_with_internal_scanner(scan_dir, ignore_to_glob(ignore_patterns))
    else:
        yield from _scan_with_ripgrep(scan_dir, ignore_patterns)


def _scan_with_ripgrep(scan_dir: Path, ignore_patterns: list[str]) -> Iterator[Path]:
    logger.info("[Refresh] Starting scan", scanner="ripgrep", scan_dir=scan_dir)

    compiled_ignore_path = scan_dir / ".TagStudio" / ".compiled_ignore"

    # Write compiled ignore patterns (built-in + user) to a temp file to pass to ripgrep
    try:
        with open(compiled_ignore_path, "w") as pattern_file:
            pattern_file.write("\n".join(ignore_patterns))
    except OSError as e:
        raise FileNotFoundError(
            f"Unable to write compiled ignore file: {compiled_ignore_path}"
        ) from e

    if not compiled_ignore_path.is_file():
        raise FileNotFoundError(f"Compiled ignore file was not created: {compiled_ignore_path}")

    process = subprocess.Popen(
        [
            "rg",
            "--files",
            "--follow",
            "--hidden",
            "--ignore-file",
            str(compiled_ignore_path),
        ],
        cwd=scan_dir,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    assert process.stdout is not None

    completed = False
    return_code: int | None = None
    try:
        for line in process.stdout:
            yield scan_dir / line.rstrip("\n")
        completed = True
    finally:
        process.stdout.close()

        if not completed and process.poll() is None:
            process.terminate()

        return_code = process.wait()
        compiled_ignore_path.unlink(missing_ok=True)

    if return_code != 0:
        logger.error(f"[Refresh] ripgrep scan failed with exit code {return_code}")


def _scan_with_internal_scanner(scan_dir: Path, ignore_patterns: list[str]) -> Iterator[Path]:
    logger.info("[Refresh] Starting scan", scanner="internal", scan_dir=scan_dir)

    try:
        yield from (
            pathlib.Path(str(scan_dir)).glob(
                "***/*", flags=PATH_GLOB_FLAGS, exclude=ignore_patterns
            )
        )
    except ValueError:
        logger.error("[Refresh] ValueError when scanning directory with internal scanner!")
