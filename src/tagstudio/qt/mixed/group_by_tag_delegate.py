# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library


class GroupByTagDelegate(QStyledItemDelegate):
    """Custom delegate for rendering tags in the Group By dropdown with decorations."""

    def __init__(self, library: "Library", parent=None):
        super().__init__(parent)
        self.library = library

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        """Paint the tag item with proper decorations."""
        # For now, use default painting - we'll enhance this later
        super().paint(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Return the size hint for the item."""
        # For now, use default size - we'll enhance this later
        return super().sizeHint(option, index)
