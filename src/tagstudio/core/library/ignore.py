# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import NamedTuple

import structlog
from wcmatch import glob

from tagstudio.core.constants import IGNORE_NAME, TS_FOLDER_NAME
from tagstudio.core.utils.singleton import Singleton

logger = structlog.get_logger()

_RULE_FLAGS: int = glob.GLOBSTAR | glob.DOTGLOB


GLOBAL_IGNORE = [
    # Trash -----------------------
    ".Trash-*",
    ".Trash",
    ".Trashes",
    "$RECYCLE.BIN",
    # System ----------------------
    "._*",
    ".DS_Store",
    ".fseventsd",
    ".Spotlight-V100",
    ".TemporaryItems",
    "desktop.ini",
    "System Volume Information",
    ".localized",
]


class _Rule(NamedTuple):
    matcher: glob.WcMatcher
    negated: bool
    dir_only: bool
    name_only: bool


def _parse_rule(pattern: str) -> _Rule | None:
    negated = pattern.startswith("!")
    pattern = pattern.removeprefix("!")
    dir_only = pattern.endswith("/")
    pattern = pattern.rstrip("/")
    if not pattern:
        return None
    # A slashed pattern is relative to the root, otherwise it matches any name
    name_only = "/" not in pattern
    pattern = pattern.removeprefix("/")
    return _Rule(glob.compile(pattern, flags=_RULE_FLAGS), negated, dir_only, name_only)


class IgnoreMatcher:
    """Matches paths relative to the library against .gitignore-style patterns."""

    def __init__(self, patterns: list[str]) -> None:
        self._rules = [rule for pattern in patterns if (rule := _parse_rule(pattern))]
        self._folder_verdicts: dict[str, bool] = {}

    def match(self, path: str, is_dir: bool) -> bool:
        """Whether `path` is ignored, without checking its parent folders."""
        name = path.rpartition("/")[2]
        for rule in reversed(self._rules):
            target = name if rule.name_only else path
            if (is_dir or not rule.dir_only) and rule.matcher.match(target):
                return not rule.negated
        return False

    def is_ignored(self, path: Path | str) -> bool:
        """Whether the file at `path` is ignored, including by any ignored parent folder."""
        parts = Path(path).as_posix().split("/")
        for depth in range(1, len(parts)):
            folder = "/".join(parts[:depth])
            if folder not in self._folder_verdicts:
                self._folder_verdicts[folder] = self.match(folder, is_dir=True)
            if self._folder_verdicts[folder]:
                return True
        return self.match("/".join(parts), is_dir=False)


def migrate_ext_list(exts: list[str], is_exclude_list: bool) -> str:
    # read template
    ts_ignore_template = (
        Path(__file__).parents[2] / "resources/templates/ts_ignore_template_blank.txt"
    )
    with open(ts_ignore_template) as f:
        out = f.read()

    # actual conversion
    prefix = ""
    if not is_exclude_list:
        prefix = "!"
        out += "*\n!*/\n"
    out += "\n".join([f"{prefix}*.{x.lstrip('.')}\n" for x in exts])
    return out


def _strip(line: str) -> str:
    """Strip a line ending and unescaped trailing whitespace from an ignore file line.

    Leading whitespace and a backslash-escaped trailing space are left intact, matching
    .gitignore's rule that trailing spaces are ignored unless escaped.
    """
    line = line.rstrip("\r\n")
    while line and line[-1].isspace() and line[-2:-1] != "\\":
        line = line[:-1]
    return line


class Ignore(metaclass=Singleton):
    """Class for processing and managing glob-like file ignore file patterns."""

    _last_loaded: tuple[Path, float] | None = None
    _patterns: list[str] = [*GLOBAL_IGNORE, TS_FOLDER_NAME]
    matcher: IgnoreMatcher = IgnoreMatcher(_patterns)

    @staticmethod
    def read_ignore_file(library_dir: Path) -> list[str]:
        """Get the entire raw '.ts_ignore' file contents as a list of strings."""
        ts_ignore_path = Path(library_dir / TS_FOLDER_NAME / IGNORE_NAME)

        if not ts_ignore_path.exists():
            logger.info(
                "[Ignore] No .ts_ignore file found",
                path=ts_ignore_path,
            )

            return []

        with open(ts_ignore_path, encoding="utf8") as f:
            return f.readlines()

    @staticmethod
    def write_ignore_file(library_dir: Path, lines: list[str]) -> None:
        """Write to the '.ts_ignore' file."""
        ts_ignore_path = Path(library_dir / TS_FOLDER_NAME / IGNORE_NAME)

        if not ts_ignore_path.exists():
            logger.info(
                "[Ignore] No .ts_ignore file found",
                path=ts_ignore_path,
            )

            return

        with open(ts_ignore_path, "w", encoding="utf8") as f:
            f.writelines(lines)

    @staticmethod
    def get_patterns(
        library_dir: Path,
        include_global: bool = True,
        update_state: bool = True,
    ) -> list[str]:
        """Get the ignore patterns for the given library directory.

        The library's .TagStudio folder always comes last so it doesn't get reincluded.

        Args:
            library_dir (Path): The path of the library to load patterns from.
            include_global (bool): Flag for including the global ignore list.
            update_state (bool): Flag for also loading the patterns into the class's state.
                Should be True outside of exceptions that may include tests, migrations, etc.
        """
        global_patterns = GLOBAL_IGNORE if include_global else []
        ts_ignore_path = Path(library_dir / TS_FOLDER_NAME / IGNORE_NAME)

        # Return computed patterns if the state of the Ignore singleton shouldn't be updated.
        if not update_state:
            return [*global_patterns, *Ignore._load_ignore_file(ts_ignore_path), TS_FOLDER_NAME]

        # Return default internal patterns if no .ts_ignore exists.
        if not ts_ignore_path.exists():
            logger.info(
                "[Ignore] No .ts_ignore file found",
                path=ts_ignore_path,
            )
            Ignore._last_loaded = None
            Ignore._patterns = [*global_patterns, TS_FOLDER_NAME]
            Ignore.matcher = IgnoreMatcher(Ignore._patterns)

            return Ignore._patterns

        # Process the .ts_ignore file if the previous result is non-existent or outdated.
        loaded = (ts_ignore_path, ts_ignore_path.stat().st_mtime)
        if Ignore._last_loaded != loaded:
            logger.info(
                "[Ignore] Processing the .ts_ignore file...",
                library=library_dir,
                last_mtime=Ignore._last_loaded[1] if Ignore._last_loaded else None,
                new_mtime=loaded[1],
            )
            user_patterns = Ignore._load_ignore_file(ts_ignore_path)
            Ignore._patterns = [*global_patterns, *user_patterns, TS_FOLDER_NAME]
            Ignore.matcher = IgnoreMatcher(Ignore._patterns)
        else:
            logger.info(
                "[Ignore] No updates to the .ts_ignore detected",
                library=library_dir,
                last_mtime=loaded[1],
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
                    line = _strip(line_raw)
                    # Ignore blank lines and comments
                    if not line or line.startswith("#"):
                        continue
                    patterns.append(line)

        return patterns
