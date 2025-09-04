# Based on the implementation by eyllanesc:
# https://stackoverflow.com/questions/54230005/qmovie-with-border-radius
# Licensed under the Creative Commons CC BY-SA 4.0 License:
# https://creativecommons.org/licenses/by-sa/4.0/
# Modified for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import override

from PySide6.QtCore import QRect
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QProxyStyle


class RoundedPixmapStyle(QProxyStyle):
    def __init__(self, radius: int = 8):
        super().__init__()
        self._radius = radius

    @override
    def drawItemPixmap(
        self, painter: QPainter, rect: QRect, alignment: int, pixmap: QPixmap | QImage
    ):
        painter.save()
        pix = QPixmap(pixmap.size())
        pix.fill(QColor("transparent"))
        p = QPainter(pix)
        p.setBrush(QBrush(pixmap))
        p.setPen(QColor("transparent"))
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.drawRoundedRect(pixmap.rect(), self._radius, self._radius)
        p.end()
        super().drawItemPixmap(painter, rect, alignment, pix)
        painter.restore()
