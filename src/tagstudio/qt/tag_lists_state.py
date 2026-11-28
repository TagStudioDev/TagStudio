# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import QObject, Signal

from tagstudio.core.constants import TS_FOLDER_NAME
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.library_state import LIBRARY_STATE_NAME, LibraryState

_RECENT_TAGS_LIMIT = 20  # TODO: Make a setting


class TagListsState(QObject):
    """A library's pinned and recent tags state."""

    pinned_tags_changed = Signal()
    recent_tags_changed = Signal()

    def __init__(self, library: Library) -> None:
        super().__init__()
        self._lib = library
        self._library_state = LibraryState()
        self._pinned_tag_ids: set[int] = set()
        self._has_unsaved_recent_tags = False

    @property
    def pinned_tag_ids(self) -> set[int]:
        return self._pinned_tag_ids

    @property
    def recent_tag_ids(self) -> list[int]:
        return self._library_state.recent_tag_ids

    def is_pinned(self, tag_id: int) -> bool:
        return tag_id in self._pinned_tag_ids

    def set_pinned(self, tag_id: int, is_pinned: bool) -> None:
        """Pin or unpin a tag in the open library."""
        if is_pinned:
            self._pinned_tag_ids.add(tag_id)
        else:
            self._pinned_tag_ids.discard(tag_id)
        self._library_state.pinned_tag_ids = sorted(self._pinned_tag_ids)
        self._library_state.save()
        self._has_unsaved_recent_tags = False
        self.pinned_tags_changed.emit()

    def add_recent_tags(self, tag_ids: list[int]) -> None:
        """Add these tags to the front of the recent tags, moving any that are already listed."""
        older_tag_ids = [
            tag_id
            for tag_id in self._library_state.recent_tag_ids
            if tag_id not in tag_ids and self._lib.get_cached_tag(tag_id) is not None
        ]
        self._library_state.recent_tag_ids = [*tag_ids, *older_tag_ids][:_RECENT_TAGS_LIMIT]
        self._has_unsaved_recent_tags = True
        self.recent_tags_changed.emit()

    def load(self) -> None:
        """Read the open library's pinned and recent tags."""
        # NOTE: Tags that don't match ones in the library are skipped.
        library_dir = unwrap(self._lib.library_dir)
        self._library_state = LibraryState.load(library_dir / TS_FOLDER_NAME / LIBRARY_STATE_NAME)
        self._pinned_tag_ids = {
            tag_id
            for tag_id in self._library_state.pinned_tag_ids
            if self._lib.get_cached_tag(tag_id) is not None
        }
        self.pinned_tags_changed.emit()
        self.recent_tags_changed.emit()

    def close(self) -> None:
        """Close the open library's tag lists, saving its recent tags if they changed."""
        if self._has_unsaved_recent_tags:
            self._library_state.save()
        self._library_state = LibraryState()
        self._pinned_tag_ids = set()
        self._has_unsaved_recent_tags = False
        self.pinned_tags_changed.emit()
        self.recent_tags_changed.emit()
