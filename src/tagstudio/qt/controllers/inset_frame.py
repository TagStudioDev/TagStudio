# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import QFrame, QWidget

from tagstudio.qt.views.styles.stylesheets import RADIUS
from tagstudio.qt.views.styles.widget_effects import SurfaceStyle, WidgetEffects


class InsetFrame(QFrame):
    """A simple darkened frame, used for conveying a negative visual layer."""

    def __init__(self, parent: QWidget | None = None, radius: float = RADIUS) -> None:
        super().__init__(parent)
        self._effect = WidgetEffects()
        self._radius = radius

    @override
    def paintEvent(self, arg__1: QPaintEvent) -> None:
        painter = QPainter(self)
        self._effect.paint_surface(painter, self.rect(), self._radius, style=SurfaceStyle.DEBOSSED)
        painter.end()
