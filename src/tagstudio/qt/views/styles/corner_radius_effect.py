# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QBrush, QPainter, QTransform
from PySide6.QtWidgets import QGraphicsEffect, QWidget


class CornerRadiusEffect(QGraphicsEffect):
    """Add an anti-aliased corner radius effect to a widget."""

    def __init__(self, parent: QWidget, radius: float) -> None:
        super().__init__(parent)
        self._radius = radius

    @override
    def draw(self, painter: QPainter) -> None:
        offset = QPoint()
        pixmap = self.sourcePixmap(
            Qt.CoordinateSystem.LogicalCoordinates, offset, QGraphicsEffect.PixmapPadMode.NoPad
        )
        if pixmap.isNull():
            return

        brush = QBrush(pixmap)
        brush.setTransform(QTransform.fromTranslate(offset.x(), offset.y()))

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(brush)
        painter.drawRoundedRect(
            QRectF(offset, pixmap.deviceIndependentSize()), self._radius, self._radius
        )
        painter.restore()
