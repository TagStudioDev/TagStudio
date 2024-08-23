# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6 import QtCore
from PySide6.QtCore import QEvent
from PySide6.QtGui import QEnterEvent, QPainter, QColor, QPen, QPainterPath, QPaintEvent
from PySide6.QtWidgets import QWidget
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper


class ThumbButton(QPushButtonWrapper):
    def __init__(self, parent: QWidget, thumb_size: tuple[int, int]) -> None:
        super().__init__(parent)
        self.thumb_size: tuple[int, int] = thumb_size
        self.hovered = False
        self.selected = False

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
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
                painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_HardLight
                )
                color = QColor("#bb4ff0")
                color.setAlphaF(0.5)
                pen = QPen(color, width)
                painter.setPen(pen)
                painter.fillPath(path, color)
                painter.drawPath(path)

                painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_Source
                )
                color = QColor("#bb4ff0") if not self.hovered else QColor("#55bbf6")
                pen = QPen(color, width)
                painter.setPen(pen)
                painter.drawPath(path)
            elif self.hovered:
                painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_Source
                )
                color = QColor("#55bbf6")
                pen = QPen(color, width)
                painter.setPen(pen)
                painter.drawPath(path)
            painter.end()

    def enterEvent(self, event: QEnterEvent) -> None:
        self.hovered = True
        self.repaint()
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.hovered = False
        self.repaint()
        return super().leaveEvent(event)

    def set_selected(self, value: bool) -> None:
        self.selected = value
        self.repaint()
