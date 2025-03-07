# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel


class ClickableLabel(QLabel):
    """A clickable Label widget."""

    clicked = Signal()

    def __init__(self):
        super().__init__()

    def mousePressEvent(self, event):  # noqa: N802
        self.clicked.emit()
