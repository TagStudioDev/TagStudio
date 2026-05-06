# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Callable

import structlog
from PySide6.QtCore import Signal

from tagstudio.qt.views.field_container_view import FieldContainerView

logger = structlog.get_logger(__name__)


class FieldContainer(FieldContainerView):
    copy: Signal = Signal()
    edit: Signal = Signal()
    remove: Signal = Signal()

    def __init__(self, title: str = "Field", inline: bool = True) -> None:
        super().__init__(title, inline)

    def _copy_callback(self) -> None:
        self.copy.emit()

    def _edit_callback(self) -> None:
        self.edit.emit()

    def _remove_callback(self) -> None:
        self.remove.emit()

    def on_copy(self, callback: Callable[[], None] | None = None) -> None:
        if callback is None:
            return

        self.copy.connect(callback)
        self.copy_enabled = True

    def on_edit(self, callback: Callable[[], None] | None = None) -> None:
        if callback is None:
            return

        self.edit.connect(callback)
        self.edit_enabled = True

    def on_remove(self, callback: Callable[[], None] | None = None) -> None:
        if callback is None:
            return

        self.remove.connect(callback)
        self.remove_enabled = True
