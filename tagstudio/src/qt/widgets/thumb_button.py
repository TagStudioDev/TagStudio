# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6 import QtCore
from PySide6.QtCore import QEvent
from PySide6.QtGui import QEnterEvent, QPainter, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QWidget, QPushButton


class ThumbButton(QPushButton):
    def __init__(self, parent: QWidget, thumb_size: tuple[int, int]) -> None:
        super().__init__(parent)
        self.thumb_size: tuple[int, int] = thumb_size
        self.hovered = False
        self.selected = False

        # self.clicked.connect(lambda checked: self.set_selected(True))

    def paintEvent(self, event: QEvent) -> None:
        super().paintEvent(event)
        if self.hovered or self.selected:
            painter = QPainter()
            painter.begin(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            # painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
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

            # color = QColor('#bb4ff0') if self.selected else QColor('#55bbf6')
            # pen = QPen(color, width)
            # painter.setPen(pen)
            # # brush.setColor(fill)
            # painter.drawPath(path)

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
