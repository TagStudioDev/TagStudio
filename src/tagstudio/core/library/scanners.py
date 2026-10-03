# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import os
import stat
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path

import structlog
from wcmatch import glob

from tagstudio.core.constants import TS_FOLDER_NAME
from tagstudio.core.library.ignore import PATH_GLOB_FLAGS, ignore_to_glob
from tagstudio.core.utils.ripgrep_status import RipgrepStatus
from tagstudio.core.utils.silent_subprocess import silent_popen  # pyright: ignore

logger = structlog.get_logger(__name__)


def scan_paths(
    scan_dir: Path, ignore_patterns: list[str], force_internal_scanner: bool = False
) -> Iterator[Path]:
    """Scan `scan_dir` for files, yielding each match's path relative to `scan_dir`.

    Uses ripgrep if present on the system, falling back to the internal (wcmatch) scanner
    otherwise or if `force_internal_scanner` is set.
    """
    if not force_internal_scanner and RipgrepStatus.which() is not None:
        yield from _scan_with_ripgrep(scan_dir, ignore_patterns)
        return
    yield from _scan_with_internal_scanner(scan_dir, ignore_patterns)


def _scan_with_ripgrep(scan_dir: Path, ignore_patterns: list[str]) -> Iterator[Path]:
    """Scan for files with ripgrep."""
    logger.info("[Scanners] Using ripgrep for scanning", path=scan_dir)

    compiled_ignore_path = scan_dir / TS_FOLDER_NAME / ".compiled_ignore"
    compiled_ignore_path.parent.mkdir(parents=True, exist_ok=True)
    compiled_ignore_path.write_text("\n".join(ignore_patterns), encoding="utf-8")

    proc: subprocess.Popen[str] | None = None
    # Writing to a temp file instead of a pipe so it doesn't get overloaded and lock up
    with tempfile.TemporaryFile(mode="w+", encoding="UTF-8") as stderr_file:
        try:
            proc = silent_popen(
                [
                    RipgrepStatus.which(),
                    "--files",  # Skip folders
                    "--follow",  # Follow symlinks
                    "--hidden",  # Scan hidden folders and files
                    "--no-ignore",  # Ignore *literal* .gitignore files in paths
                    "--ignore-file",  # Pass the .ts_ignore file:
                    str(compiled_ignore_path),
                ],
                cwd=scan_dir,
                stdout=subprocess.PIPE,
                stderr=stderr_file,
                text=True,
                encoding="UTF-8",
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip("\n")
                if not line:
                    continue
                yield Path(line)

            proc.wait()
            if proc.returncode not in (0, 1):  # 1 == "no matches", still successful
                stderr_file.seek(0)
                logger.error(
                    "[Scanners] ripgrep exited with an error",
                    returncode=proc.returncode,
                    stderr=stderr_file.read(),
                )
        finally:
            if proc is not None:
                # Loop finished
                if proc.stdout is not None:
                    proc.stdout.close()
                # Still running, but cancelled mid-loop
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait()
            try:
                compiled_ignore_path.unlink(missing_ok=True)
            except OSError as e:
                logger.error(
                    "[Scanners] Could not remove compiled ignore path",
                    path=compiled_ignore_path,
                    error=e,
                )


def _scan_with_internal_scanner(scan_dir: Path, ignore_patterns: list[str]) -> Iterator[Path]:
    """Scan for files with the internal scanner."""
    logger.info("[Scanners] Using internal scanner for scanning", path=scan_dir)
    matcher = glob.compile(patterns=ignore_to_glob(ignore_patterns), flags=PATH_GLOB_FLAGS)

    def walk(dir_path: Path, ancestors: frozenset[str]) -> Iterator[Path]:
        try:
            dir_items = list(os.scandir(dir_path))
        except OSError as e:
            logger.error("[Scanners] Could not scan directory", path=dir_path, error=e)
            return

        for item in dir_items:
            rel = Path(item.path).relative_to(scan_dir)
            if matcher.match(rel.as_posix()):
                continue
            try:
                item_stat = item.stat(follow_symlinks=True)
            except OSError:
                continue

            # Check for and handle cyclical symlinks
            if stat.S_ISDIR(item_stat.st_mode):
                key = os.path.realpath(item.path)
                if key not in ancestors:
                    yield from walk(Path(item.path), ancestors | {key})
            else:
                yield rel

    yield from walk(scan_dir, frozenset({os.path.realpath(scan_dir)}))
