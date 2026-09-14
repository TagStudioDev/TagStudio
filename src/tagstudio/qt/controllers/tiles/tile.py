# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from typing import override
from warnings import catch_warnings

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent, QResizeEvent
from PySide6.QtWidgets import QWidget

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.views.styles.stylesheets import container_style, header
from tagstudio.qt.views.tiles.tile_view import TileView


class Tile(QWidget):
    """Wraps a title, action buttons, and data such as text or tags inside a single widget."""

    def __init__(self, title: str = "TILE") -> None:
        super().__init__()
        self.setObjectName("tile")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.title: str = title
        self.copy_callback: Callable[[], None] | None = None
        self.edit_callback: Callable[[], None] | None = None
        self.remove_callback: Callable[[], None] | None = None

        self.setLayout(TileView())
        self.set_title(title)
        self.setStyleSheet(container_style())

    @override
    def layout(self) -> TileView:
        return super().layout()  # pyright: ignore[reportReturnType]

    def set_copy_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.layout().copy_button.clicked.disconnect()

        self.copy_callback = callback
        if callback:
            self.layout().copy_button.clicked.connect(callback)

    def set_edit_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.layout().edit_button.clicked.disconnect()

        self.edit_callback = callback
        if callback:
            self.layout().edit_button.clicked.connect(callback)

    def set_remove_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.layout().remove_button.clicked.disconnect()

        self.remove_callback = callback
        if callback:
            self.layout().remove_button.clicked.connect(callback)

    def set_inner_widget(self, widget: QWidget) -> None:
        if item := self.layout().data_layout.itemAt(0):
            old: QWidget = unwrap(item.widget())
            self.layout().data_layout.removeWidget(old)
            old.deleteLater()

        self.layout().data_layout.addWidget(widget)

    def get_inner_widget(self) -> QWidget | None:
        if item := self.layout().data_layout.itemAt(0):
            return item.widget()
        return None

    def set_title(self, title: str) -> None:
        self.title = header(title, 4)
        self.layout().title_widget.setText(self.title)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        # NOTE: You could pass the hover event to the inner widget if needed.
        if self.copy_callback:
            self.layout().copy_button.setHidden(False)
        if self.edit_callback:
            self.layout().edit_button.setHidden(False)
        if self.remove_callback:
            self.layout().remove_button.setHidden(False)
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        if self.copy_callback:
            self.layout().copy_button.setHidden(True)
        if self.edit_callback:
            self.layout().edit_button.setHidden(True)
        if self.remove_callback:
            self.layout().remove_button.setHidden(True)
        return super().leaveEvent(event)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.layout().title_widget.setFixedWidth(int(event.size().width() // 1.5))
        return super().resizeEvent(event)
