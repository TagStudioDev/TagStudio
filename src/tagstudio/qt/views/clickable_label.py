# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import override

from PySide6.QtCore import Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel


class ClickableLabel(QLabel):
    """A clickable QLabel widget."""

    clicked = Signal()

    def __init__(self):
        super().__init__()

    @override
    def mousePressEvent(self, ev: QMouseEvent):
        self.clicked.emit()
