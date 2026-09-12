# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import subprocess
from collections.abc import Iterator
from pathlib import Path

import structlog
from wcmatch import pathlib

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
    try:
        proc = silent_popen(
            [
                RipgrepStatus.which(),
                "--files",
                "--follow",
                "--hidden",
                "--ignore-file",
                str(compiled_ignore_path),
            ],
            cwd=scan_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="UTF-8",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip("\n")
            if not line:
                continue
            path = Path(line)
            if (scan_dir / path).is_dir():
                continue
            yield path

        proc.wait()
        if proc.returncode not in (0, 1):  # 1 == "no matches", still successful
            logger.error(
                "[Scanners] ripgrep exited with an error",
                returncode=proc.returncode,
                stderr=proc.stderr.read() if proc.stderr else "",
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
    """Scan for files with the internal glob-based scanner (wcmatch)."""
    logger.info("[Scanners] Using internal scanner for scanning", path=scan_dir)

    glob_patterns = ignore_to_glob(ignore_patterns)
    try:
        for f in pathlib.Path(str(scan_dir)).glob(
            "***/*", flags=PATH_GLOB_FLAGS, exclude=glob_patterns
        ):
            if f.is_dir():
                continue
            path = Path(f).relative_to(scan_dir)
            yield path
    except ValueError:
        logger.error("[Scanners] ValueError while scanning directory with the internal scanner")
