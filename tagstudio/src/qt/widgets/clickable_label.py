# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from src.qt.core import QLabel, Signal


class ClickableLabel(QLabel):
    """A clickable Label widget."""

    clicked = Signal()

    def __init__(self):
        super().__init__()

    def mousePressEvent(self, event):  # noqa: N802
        self.clicked.emit()
