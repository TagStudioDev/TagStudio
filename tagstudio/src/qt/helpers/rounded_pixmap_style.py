# Based on the implementation by eyllanesc:
# https://stackoverflow.com/questions/54230005/qmovie-with-border-radius
# Licensed under the Creative Commons CC BY-SA 4.0 License:
# https://creativecommons.org/licenses/by-sa/4.0/
# Modified for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtGui import QBrush, QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QProxyStyle,
)


class RoundedPixmapStyle(QProxyStyle):
    def __init__(self, radius=8):
        super().__init__()
        self._radius = radius

    def drawItemPixmap(self, painter, rectangle, alignment, pixmap):  # noqa: N802
        painter.save()
        pix = QPixmap(pixmap.size())
        pix.fill(QColor("transparent"))
        p = QPainter(pix)
        p.setBrush(QBrush(pixmap))
        p.setPen(QColor("transparent"))
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.drawRoundedRect(pixmap.rect(), self._radius, self._radius)
        p.end()
        super().drawItemPixmap(painter, rectangle, alignment, pix)
        painter.restore()
