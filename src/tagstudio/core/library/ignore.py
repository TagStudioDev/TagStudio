# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from copy import deepcopy
from pathlib import Path

import structlog
from wcmatch import glob, pathlib

from tagstudio.core.constants import IGNORE_NAME, TS_FOLDER_NAME
from tagstudio.core.singleton import Singleton

logger = structlog.get_logger()

PATH_GLOB_FLAGS = glob.GLOBSTARLONG | glob.DOTGLOB | glob.NEGATE | pathlib.MATCHBASE


def _ignore_to_glob(ignore_patterns: list[str]) -> list[str]:
    """Convert .gitignore-like patterns to explicit glob syntax.

    Args:
        ignore_patterns (list[str]): The .gitignore-like patterns to convert.
    """
    glob_patterns: list[str] = deepcopy(ignore_patterns)
    additional_patterns: list[str] = []

    # Mimic implicit .gitignore syntax behavior for the SQLite GLOB function.
    for pattern in glob_patterns:
        # Temporarily remove any exclusion character before processing
        exclusion_char = ""
        gp = pattern
        if pattern.startswith("!"):
            gp = pattern[1:]
            exclusion_char = "!"

        if not gp.startswith("**/") and not gp.startswith("*/") and not gp.startswith("/"):
            # Create a version of a prefix-less pattern that starts with "**/"
            gp = "**/" + gp
            additional_patterns.append(exclusion_char + gp)

            gp = gp.removesuffix("/**").removesuffix("/*").removesuffix("/")
            additional_patterns.append(exclusion_char + gp)

            gp = gp.removeprefix("**/").removeprefix("*/")
            additional_patterns.append(exclusion_char + gp)

    glob_patterns = glob_patterns + additional_patterns

    # Add "/**" suffix to suffix-less patterns to match implicit .gitignore behavior.
    for pattern in glob_patterns:
        if pattern.endswith("/**"):
            continue

        glob_patterns.append(pattern.removesuffix("/*").removesuffix("/") + "/**")

    glob_patterns = list(set(glob_patterns))

    logger.info("[Ignore]", glob_patterns=glob_patterns)
    return glob_patterns


GLOBAL_IGNORE = _ignore_to_glob(
    [
        # TagStudio -------------------
        f"{TS_FOLDER_NAME}",
        # System Trashes --------------
        ".Trash",
        ".Trash-*",
        ".Trashes",
        "$RECYCLE.BIN",
        # macOS Generated -------------
        "._*",
        ".DS_Store",
        ".fseventsd",
        ".Spotlight-V100",
        ".TemporaryItems",
        "System Volume Information",
    ]
)


class Ignore(metaclass=Singleton):
    """Class for processing and managing glob-like file ignore file patterns."""

    _last_loaded: tuple[Path, float] | None = None
    _patterns: list[str] = []

    @staticmethod
    def get_patterns(library_dir: Path, include_global: bool = True) -> list[str]:
        """Get the ignore patterns for the given library directory.

        Args:
            library_dir (Path): The path of the library to load patterns from.
            include_global (bool): Flag for including the global ignore set.
                In most scenarios, this should be True.
        """
        patterns = GLOBAL_IGNORE if include_global else []
        ts_ignore_path = Path(library_dir / TS_FOLDER_NAME / IGNORE_NAME)

        if not ts_ignore_path.exists():
            logger.info(
                "[Ignore] No .ts_ignore file found",
                path=ts_ignore_path,
            )
            Ignore._last_loaded = None
            Ignore._patterns = patterns

            return Ignore._patterns

        # Process the .ts_ignore file if the previous result is non-existent or outdated.
        loaded = (ts_ignore_path, ts_ignore_path.stat().st_mtime)
        if not Ignore._last_loaded or (Ignore._last_loaded and Ignore._last_loaded != loaded):
            logger.info(
                "[Ignore] Processing the .ts_ignore file...",
                library=library_dir,
                last_mtime=Ignore._last_loaded[1] if Ignore._last_loaded else None,
                new_mtime=loaded[1],
            )
            Ignore._patterns = _ignore_to_glob(patterns + Ignore._load_ignore_file(ts_ignore_path))
        else:
            logger.info(
                "[Ignore] No updates to the .ts_ignore detected",
                library=library_dir,
                last_mtime=Ignore._last_loaded[1],
                new_mtime=loaded[1],
            )
        Ignore._last_loaded = loaded

        return Ignore._patterns

    @staticmethod
    def _load_ignore_file(path: Path) -> list[str]:
        """Load and process the .ts_ignore file into a list of glob patterns.

        Args:
            path (Path): The path of the .ts_ignore file.
        """
        patterns: list[str] = []
        if path.exists():
            with open(path, encoding="utf8") as f:
                for line_raw in f.readlines():
                    line = line_raw.strip()
                    # Ignore blank lines and comments
                    if not line or line.startswith("#"):
                        continue
                    patterns.append(line)

        return patterns
