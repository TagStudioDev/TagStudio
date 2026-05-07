# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Callable

import structlog
from PySide6.QtCore import Signal

from tagstudio.qt.views.field_container_view import FieldContainerView

logger = structlog.get_logger(__name__)


class FieldContainer(FieldContainerView):
    """A container that holds a field widget and provides some relevant information and controls."""

    __on_copy: Signal = Signal()
    __on_edit: Signal = Signal()
    __on_remove: Signal = Signal()

    def __init__(self, title: str = "Field", inline: bool = True) -> None:
        super().__init__(title, inline)

    def _copy_callback(self) -> None:
        self.__on_copy.emit()

    def _edit_callback(self) -> None:
        self.__on_edit.emit()

    def _remove_callback(self) -> None:
        self.__on_remove.emit()

    def on_copy(self, callback: Callable[[], None] | None = None) -> None:
        """Connects a callback to the copy signal."""
        if callback is None:
            return

        self.__on_copy.connect(callback)
        self.copy_enabled = True

    def on_edit(self, callback: Callable[[], None] | None = None) -> None:
        """Connects a callback to the edit signal."""
        if callback is None:
            return

        self.__on_edit.connect(callback)
        self.edit_enabled = True

    def on_remove(self, callback: Callable[[], None] | None = None) -> None:
        """Connects a callback to the remove signal."""
        if callback is None:
            return

        self.__on_remove.connect(callback)
        self.remove_enabled = True
