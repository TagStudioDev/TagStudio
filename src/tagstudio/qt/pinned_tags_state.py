# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import QObject, Signal

from tagstudio.core.constants import TS_FOLDER_NAME
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.library_state import LIBRARY_STATE_NAME, LibraryState


class PinnedTagsState(QObject):
    """The open library's pinned tags, saved in its library state file."""

    changed = Signal()

    def __init__(self, library: Library) -> None:
        super().__init__()
        self._lib = library
        self._library_state = LibraryState()
        self._tag_ids: set[int] = set()

    @property
    def tag_ids(self) -> set[int]:
        return self._tag_ids

    def is_pinned(self, tag_id: int) -> bool:
        return tag_id in self._tag_ids

    def set_pinned(self, tag_id: int, is_pinned: bool) -> None:
        """Pin or unpin a tag in the open library."""
        if is_pinned:
            self._tag_ids.add(tag_id)
        else:
            self._tag_ids.discard(tag_id)
        self._library_state.pinned_tag_ids = sorted(self._tag_ids)
        self._library_state.save()
        self.changed.emit()

    def load(self) -> None:
        """Read the open library's pinned tags."""
        # NOTE: Tags that don't match ones in the library are skipped.
        library_dir = unwrap(self._lib.library_dir)
        self._library_state = LibraryState.load(library_dir / TS_FOLDER_NAME / LIBRARY_STATE_NAME)
        self._tag_ids = {
            tag_id
            for tag_id in self._library_state.pinned_tag_ids
            if self._lib.get_cached_tag(tag_id) is not None
        }
        self.changed.emit()

    def clear(self) -> None:
        self._library_state = LibraryState()
        self._tag_ids = set()
        self.changed.emit()
