# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from tagstudio.core.library.alchemy.library import Entry, Library
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger(__name__)


@dataclass
class IgnoredRegistry:
    """State tracker for ignored entries."""

    lib: Library
    ignored_entries: list[Entry] = field(default_factory=list)

    @property
    def ignored_count(self) -> int:
        return len(self.ignored_entries)

    def reset(self):
        self.ignored_entries.clear()

    def refresh_ignored_entries(self) -> Iterator[int]:
        """Track the number of entries that would otherwise be ignored by the current rules."""
        logger.info("[IgnoredRegistry] Refreshing ignored entries...")

        self.ignored_entries = []
        library_dir: Path = unwrap(self.lib.library_dir)

        for i, entry in enumerate(self.lib.all_entries()):
            if not Ignore.compiled_patterns:
                # If the compiled_patterns has malfunctioned, don't consider that a false positive
                yield i
            elif Ignore.compiled_patterns.match(library_dir / entry.path):
                self.ignored_entries.append(entry)
            yield i

    def remove_ignored_entries(self) -> None:
        self.lib.remove_entries(list(map(lambda ignored: ignored.id, self.ignored_entries)))
        self.ignored_entries = []
