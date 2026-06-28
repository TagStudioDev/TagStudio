# SPDX-FileCopyrightText: (c) 2019 Edwin Yllanes
# SPDX-License-Identifier: CC-BY-SA-4.0
# See: https://stackoverflow.com/questions/54230005/qmovie-with-border-radius/54231484#54231484


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
