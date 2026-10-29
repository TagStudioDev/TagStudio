# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.views.styles.palette import Palette
from tagstudio.qt.views.underlined_widget_view import UnderlinedWidgetView


class UnderlinedWidget(QWidget):
    """A container for a widget and an underline indicator."""

    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self.setLayout(UnderlinedWidgetView(widget))

    def toggle_underline(self, is_hidden: bool) -> None:
        self.layout().underline.setHidden(is_hidden)

    @property
    def widget(self) -> QWidget:
        return unwrap(unwrap(self.layout().itemAt(0)).widget())

    @override
    def layout(self) -> UnderlinedWidgetView:
        layout = super().layout()
        assert isinstance(layout, UnderlinedWidgetView)
        return layout

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        underline = self.layout().underline
        if underline.isHidden():
            return
        radius = underline.height() / 2
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Palette.accent())
        painter.drawRoundedRect(QRectF(underline.geometry()), radius, radius)
        painter.end()
