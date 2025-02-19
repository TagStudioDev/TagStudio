# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import sys

from PySide6 import QtCore
from PySide6.QtCore import QEvent
from PySide6.QtGui import (
    QColor,
    QEnterEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPalette,
    QPen,
)
from PySide6.QtWidgets import QWidget
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper


class ThumbButton(QPushButtonWrapper):
    def __init__(self, parent: QWidget, thumb_size: tuple[int, int]) -> None:  # noqa: N802
        super().__init__(parent)
        self.thumb_size: tuple[int, int] = thumb_size
        self.hovered = False
        self.selected = False

        # NOTE: As of PySide 6.8.0.1, the QPalette.ColorRole.Accent role no longer works on Windows.
        # The QPalette.ColorRole.AlternateBase does for some reason, but not on macOS.
        self.select_color: QColor
        if sys.platform == "win32":
            self.select_color = QPalette.color(
                self.palette(),
                QPalette.ColorGroup.Active,
                QPalette.ColorRole.AlternateBase,
            )
            self.select_color.setHsl(
                self.select_color.hslHue(),
                self.select_color.hslSaturation(),
                max(self.select_color.lightness(), 100),
                255,
            )
        else:
            self.select_color = QPalette.color(
                self.palette(),
                QPalette.ColorGroup.Active,
                QPalette.ColorRole.Accent,
            )

        self.select_color_faded: QColor = QColor(self.select_color)
        self.select_color_faded.setHsl(
            self.select_color_faded.hslHue(),
            self.select_color_faded.hslSaturation(),
            max(self.select_color_faded.lightness(), 127),
            127,
        )

        self.hover_color: QColor
        if sys.platform == "win32":
            self.hover_color = QPalette.color(
                self.palette(),
                QPalette.ColorGroup.Active,
                QPalette.ColorRole.AlternateBase,
            )
            self.hover_color.setHsl(
                self.hover_color.hslHue(),
                self.hover_color.hslSaturation(),
                max(self.hover_color.lightness(), 100),
                255,
            )
        else:
            self.hover_color = QPalette.color(
                self.palette(),
                QPalette.ColorGroup.Active,
                QPalette.ColorRole.Accent,
            )

        self.hover_color.setHsl(
            self.hover_color.hslHue(),
            self.hover_color.hslSaturation(),
            min(self.hover_color.lightness() + 80, 255),
            self.hover_color.alpha(),
        )

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
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

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        self.hovered = True
        self.repaint()
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        self.hovered = False
        self.repaint()
        return super().leaveEvent(event)

    def set_selected(self, value: bool) -> None:  # noqa: N802
        self.selected = value
        self.repaint()
