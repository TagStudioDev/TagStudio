# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Iterable

import structlog
from PySide6.QtCore import QObject, Signal

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.library.alchemy.library import Library

logger = structlog.get_logger(__name__)


def _id_set(ids: int | Iterable[int]) -> set[int]:
    return {ids} if isinstance(ids, int) else set(ids)


class EntryState(QObject):
    """Manages the state of attributes like tags for entries.

    Adding/removing tags to/from entries via the UI routes through here, and emits signals when tags
    trigger relevant UI updates like item thumbnail badge updates.
    """

    tags_changed = Signal(set)

    def __init__(self, library: Library) -> None:
        super().__init__()
        self._lib = library
        self._badge_tag_ids: tuple[int, ...] = (TAG_FAVORITE, TAG_ARCHIVED)
        self._entries_with_badge: dict[int, set[int]] = {
            tag_id: set() for tag_id in self._badge_tag_ids
        }
        self._badges_loaded: set[int] = set()

    @property
    def badge_tag_ids(self) -> tuple[int, ...]:
        return self._badge_tag_ids

    def load_badges(self, entry_ids: Iterable[int]) -> None:
        """Read which entries have the tags used for badges."""
        entry_ids = set(entry_ids)
        if not entry_ids:
            return

        tag_entries = self._lib.get_tag_entries(self._badge_tag_ids, list(entry_ids))
        for tag_id, entries in self._entries_with_badge.items():
            entries.difference_update(entry_ids)
            entries.update(tag_entries[tag_id])
        self._badges_loaded.update(entry_ids)

    def unload_badges(self) -> None:
        for entries in self._entries_with_badge.values():
            entries.clear()
        self._badges_loaded.clear()

    def has_badge(self, entry_id: int, tag_id: int) -> bool:
        if tag_id not in self._entries_with_badge:
            logger.warning("[EntryState] Tag is not used for badges", tag_id=tag_id)
            return False
        if entry_id not in self._badges_loaded:
            self.load_badges([entry_id])
        return entry_id in self._entries_with_badge[tag_id]

    def set_tag(self, entry_ids: int | Iterable[int], tag_id: int, value: bool) -> None:
        if value:
            self.add_tags(entry_ids, tag_id)
        else:
            self.remove_tags(entry_ids, tag_id)

    def add_tags(self, entry_ids: int | Iterable[int], tag_ids: int | Iterable[int]) -> None:
        """Add tags to one or more entries."""
        entry_ids_, tag_ids_ = _id_set(entry_ids), _id_set(tag_ids)
        self._lib.add_tags_to_entries(entry_ids_, tag_ids_)
        self._update(entry_ids_, tag_ids_, has_tag=True)

    def remove_tags(self, entry_ids: int | Iterable[int], tag_ids: int | Iterable[int]) -> None:
        """Remove tags from one or more entries."""
        entry_ids_, tag_ids_ = _id_set(entry_ids), _id_set(tag_ids)
        self._lib.remove_tags_from_entries(entry_ids_, tag_ids_)
        self._update(entry_ids_, tag_ids_, has_tag=False)

    def _update(self, entry_ids: set[int], tag_ids: set[int], has_tag: bool) -> None:
        for tag_id in tag_ids.intersection(self._badge_tag_ids):
            if has_tag:
                self._entries_with_badge[tag_id].update(entry_ids)
            else:
                self._entries_with_badge[tag_id].difference_update(entry_ids)
        self.tags_changed.emit(entry_ids)
