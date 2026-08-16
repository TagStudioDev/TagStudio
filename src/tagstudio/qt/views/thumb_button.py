# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6 import QtCore
from PySide6.QtCore import QEvent
from PySide6.QtGui import QColor, QEnterEvent, QPainter, QPainterPath, QPaintEvent, QPen
from PySide6.QtWidgets import QPushButton, QWidget

from tagstudio.qt.views.styles.palette import Palette


# TODO: Use newer MVC style guidelines
class ThumbButton(QPushButton):
    def __init__(self, parent: QWidget, thumb_size: tuple[int, int]) -> None:
        super().__init__(parent)
        self.thumb_size: tuple[int, int] = thumb_size
        self.hovered = False
        self.selected = False
        self.select_color = Palette.accent()

        self.select_color_faded = Palette.accent()
        self.select_color_faded.setHsl(
            self.select_color_faded.hslHue(),
            self.select_color_faded.hslSaturation(),
            max(self.select_color_faded.lightness(), 127),
            127,
        )

        self.hover_color = Palette.accent()
        self.hover_color.setHsl(
            self.hover_color.hslHue(),
            self.hover_color.hslSaturation(),
            min(self.hover_color.lightness() + 80, 255),
            self.hover_color.alpha(),
        )

    @override
    def paintEvent(self, arg__1: QPaintEvent) -> None:
        super().paintEvent(arg__1)
        if self.hovered or self.selected:
            painter = QPainter()
            painter.begin(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            width = 3
            radius = 6
            path.addRoundedRect(
                QtCore.QRectF(
                    width / 2,
                    width / 2,
                    self.thumb_size[0] - width,
                    self.thumb_size[1] - width,
                ),
                radius,
                radius,
            )

            if self.selected:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_HardLight)
                pen = QPen(self.select_color_faded, width)
                painter.setPen(pen)
                painter.fillPath(path, self.select_color_faded)
                painter.drawPath(path)

                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
                color: QColor = self.select_color if not self.hovered else self.hover_color
                pen = QPen(color, width)
                painter.setPen(pen)
                painter.drawPath(path)
            elif self.hovered:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
                pen = QPen(self.hover_color, width)
                painter.setPen(pen)
                painter.drawPath(path)

            painter.end()

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self.hovered = True
        self.repaint()
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self.hovered = False
        self.repaint()
        return super().leaveEvent(event)

    def set_selected(self, value: bool) -> None:
        if value != self.selected:
            self.selected = value
            self.repaint()
