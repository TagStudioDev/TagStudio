# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Iterable

import structlog
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QThreadPool, Signal

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

    entry_tags_changed = Signal(set)  # IDs of entries that have had their applied tags updated
    tags_edited = Signal(set)  # IDs of tags that have been edited
    # (Entry IDs, Added Tag IDs, Removed Tag IDs, Success)
    _write_finished = Signal(set, set, set, bool)

    def __init__(self, library: Library, write_pool: QThreadPool) -> None:
        super().__init__()
        self._lib = library
        self._badge_tag_ids: tuple[int, ...] = (TAG_FAVORITE, TAG_ARCHIVED)
        self._entries_with_badge: dict[int, set[int]] = {
            tag_id: set() for tag_id in self._badge_tag_ids
        }
        self._badges_loaded: set[int] = set()
        # [(Entry IDs, Added Tag IDs, Removed Tag IDs)]
        self._pending_writes: list[tuple[set[int], set[int], set[int]]] = []
        self._write_pool = write_pool
        self._write_finished.connect(self._on_write_finished)
        library.tag_edit_callbacks.append(self.tags_edited.emit)

    @property
    def badge_tag_ids(self) -> tuple[int, ...]:
        return self._badge_tag_ids

    def load_badges(self, entry_ids: Iterable[int]) -> None:
        """Read which entries have tags used for badges."""
        entry_ids = set(entry_ids)
        if entry_ids:
            tag_entries = self._lib.get_tag_entries(self._badge_tag_ids, list(entry_ids))
            self.cache_badges(entry_ids, tag_entries)

    def cache_badges(self, entry_ids: Iterable[int], tag_entries: dict[int, set[int]]) -> None:
        """Cache which entries have tags used for badges, as given by `tag_entries`."""
        entry_ids = set(entry_ids)
        for tag_id, entries in self._entries_with_badge.items():
            entries.difference_update(entry_ids)
            entries.update(entry_ids.intersection(tag_entries[tag_id]))
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
        cached_tag_ids: set[int] = (
            {tag_id} if entry_id in self._entries_with_badge[tag_id] else set()
        )
        return tag_id in self.tag_ids_with_pending_writes(entry_id, cached_tag_ids)

    def set_tag(self, entry_ids: int | Iterable[int], tag_id: int, value: bool) -> None:
        if value:
            self.add_tags(entry_ids, tag_id)
        else:
            self.remove_tags(entry_ids, tag_id)

    def add_tags(self, entry_ids: int | Iterable[int], tag_ids: int | Iterable[int]) -> None:
        """Add tags to one or more entries."""
        self._update_entry_tags(
            _id_set(entry_ids), added_tag_ids=_id_set(tag_ids), removed_tag_ids=set()
        )

    def remove_tags(self, entry_ids: int | Iterable[int], tag_ids: int | Iterable[int]) -> None:
        """Remove tags from one or more entries."""
        self._update_entry_tags(
            _id_set(entry_ids), added_tag_ids=set(), removed_tag_ids=_id_set(tag_ids)
        )

    def wait_for_writes(self) -> None:
        """Block until every queued tag write has finished and been applied."""
        self._write_pool.waitForDone()
        QCoreApplication.sendPostedEvents(self, QEvent.Type.MetaCall)

    def tag_ids_with_pending_writes(self, entry_id: int, tag_ids: set[int]) -> set[int]:
        """Apply an entry's pending tag writes to its cached tag IDs."""
        tag_ids = set(tag_ids)
        for entry_ids, added_tag_ids, removed_tag_ids in self._pending_writes:
            if entry_id in entry_ids:
                tag_ids.update(added_tag_ids)
                tag_ids.difference_update(removed_tag_ids)
        return tag_ids

    def _update_entry_tags(
        self, entry_ids: set[int], added_tag_ids: set[int], removed_tag_ids: set[int]
    ) -> None:
        """Add and/or remove tags from a set of entries."""
        self._pending_writes.append((entry_ids, added_tag_ids, removed_tag_ids))

        def write() -> None:
            success = True
            try:
                if added_tag_ids:
                    self._lib.add_tags_to_entries(entry_ids, added_tag_ids)
                if removed_tag_ids:
                    self._lib.remove_tags_from_entries(entry_ids, removed_tag_ids)
            except Exception as e:
                logger.error(
                    "[EntryState] Could not update tags on entries",
                    entry_ids=entry_ids,
                    added_tag_ids=added_tag_ids,
                    removed_tag_ids=removed_tag_ids,
                    error=e,
                )
                success = False
            self._write_finished.emit(entry_ids, added_tag_ids, removed_tag_ids, success)

        self.entry_tags_changed.emit(entry_ids)
        self._write_pool.start(write)

    def _on_write_finished(
        self, entry_ids: set[int], added_tag_ids: set[int], removed_tag_ids: set[int], success: bool
    ) -> None:
        self._pending_writes.remove((entry_ids, added_tag_ids, removed_tag_ids))
        if success:
            self._update_badges(entry_ids, added_tag_ids, removed_tag_ids)
        self.entry_tags_changed.emit(entry_ids)

    def _update_badges(
        self, entry_ids: set[int], added_tag_ids: set[int], removed_tag_ids: set[int]
    ) -> None:
        for tag_id in added_tag_ids.intersection(self._badge_tag_ids):
            self._entries_with_badge[tag_id].update(entry_ids)
        for tag_id in removed_tag_ids.intersection(self._badge_tag_ids):
            self._entries_with_badge[tag_id].difference_update(entry_ids)
