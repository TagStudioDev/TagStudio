# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from typing import override
from warnings import catch_warnings

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QPushButton, QWidget

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, container_style, header
from tagstudio.qt.views.tiles.tile_view import TileView


class Tile(QWidget):
    """Wraps a title, action buttons, and data such as text or tags inside a single widget."""

    def __init__(self, title: str = "TILE") -> None:
        super().__init__()
        self.setObjectName("tile")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.copy_callback: Callable[[], None] | None = None
        self.edit_callback: Callable[[], None] | None = None
        self.remove_callback: Callable[[], None] | None = None

        self.setLayout(TileView())
        self.set_title(title)
        self.setStyleSheet(container_style())

    @override
    def layout(self) -> TileView:
        layout = super().layout()
        assert isinstance(layout, TileView)
        return layout

    def set_copy_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.layout().copy_button.clicked.disconnect()

        self.copy_callback = callback
        self._keep_button_space(self.layout().copy_button, keep=callback is not None)
        if callback:
            self.layout().copy_button.clicked.connect(callback)

    def set_edit_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.layout().edit_button.clicked.disconnect()

        self.edit_callback = callback
        self._keep_button_space(self.layout().edit_button, keep=callback is not None)
        if callback:
            self.layout().edit_button.clicked.connect(callback)

    def set_remove_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.layout().remove_button.clicked.disconnect()

        self.remove_callback = callback
        self._keep_button_space(self.layout().remove_button, keep=callback is not None)
        if callback:
            self.layout().remove_button.clicked.connect(callback)

    def _keep_button_space(self, button: QPushButton, keep: bool) -> None:
        policy = button.sizePolicy()
        policy.setRetainSizeWhenHidden(keep)
        button.setSizePolicy(policy)

    def set_inner_widget(self, widget: QWidget) -> None:
        if item := self.layout().data_layout.itemAt(0):
            old: QWidget = unwrap(item.widget())
            self.layout().data_layout.removeWidget(old)
            # NOTE: Hide before deleteLater() or it paints over the new widget
            old.hide()
            old.deleteLater()

        self.layout().data_layout.addWidget(widget)
        # NOTE: Show now or the Tile is sized without it for a frame
        widget.show()

    def get_inner_widget(self) -> QWidget | None:
        if item := self.layout().data_layout.itemAt(0):
            return item.widget()
        return None

    def set_content_inset(self, inset: int) -> None:
        """Inset the tile's content from its left edge."""
        layout = self.layout()
        layout.inner_layout.setContentsMargins(inset, 0, 0, HALF_PAD)
        layout.title_layout.setContentsMargins(HALF_PAD - inset, 0, 0, 0)

    def set_title(self, title: str) -> None:
        self.title = header(title, 4)
        self.layout().title_widget.setText(self.title)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        # NOTE: You could pass the hover event to the inner widget if needed.
        layout = self.layout()
        if self.copy_callback:
            layout.copy_button.setHidden(False)
        if self.edit_callback:
            layout.edit_button.setHidden(False)
        if self.remove_callback:
            layout.remove_button.setHidden(False)
        # NOTE: Leaving for a context menu skips hover events
        self.update()
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        layout = self.layout()
        if self.copy_callback:
            layout.copy_button.setHidden(True)
        if self.edit_callback:
            layout.edit_button.setHidden(True)
        if self.remove_callback:
            layout.remove_button.setHidden(True)
        self.update()
        return super().leaveEvent(event)
