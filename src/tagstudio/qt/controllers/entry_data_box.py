# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from typing import override
from warnings import catch_warnings

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent, QResizeEvent
from PySide6.QtWidgets import QWidget

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.views.entry_data_box_view import EntryDataBoxView
from tagstudio.qt.views.styles.stylesheets import container_style, header


class EntryDataBox(QWidget):
    def __init__(self, title: str = "DATA BOX") -> None:
        super().__init__()
        self.setObjectName("entry_data_box")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.title: str = title
        self.copy_callback: Callable[[], None] | None = None
        self.edit_callback: Callable[[], None] | None = None
        self.remove_callback: Callable[[], None] | None = None

        self.view = EntryDataBoxView()
        self.setLayout(self.view)
        self.set_title(title)
        self.setStyleSheet(container_style())

    def set_copy_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.view.copy_button.clicked.disconnect()

        self.copy_callback = callback
        if callback:
            self.view.copy_button.clicked.connect(callback)

    def set_edit_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.view.edit_button.clicked.disconnect()

        self.edit_callback = callback
        if callback:
            self.view.edit_button.clicked.connect(callback)

    def set_remove_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.view.remove_button.clicked.disconnect()

        self.remove_callback = callback
        if callback:
            self.view.remove_button.clicked.connect(callback)

    def set_inner_widget(self, widget: QWidget) -> None:
        if item := self.view.data_layout.itemAt(0):
            old: QWidget = unwrap(item.widget())
            self.view.data_layout.removeWidget(old)
            old.deleteLater()

        self.view.data_layout.addWidget(widget)

    def get_inner_widget(self) -> QWidget | None:
        if item := self.view.data_layout.itemAt(0):
            return item.widget()
        return None

    def set_title(self, title: str) -> None:
        self.title = header(title, 4)
        self.view.title_widget.setText(self.title)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        # NOTE: You could pass the hover event to the EntryDataBox if needed.
        if self.copy_callback:
            self.view.copy_button.setHidden(False)
        if self.edit_callback:
            self.view.edit_button.setHidden(False)
        if self.remove_callback:
            self.view.remove_button.setHidden(False)
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        if self.copy_callback:
            self.view.copy_button.setHidden(True)
        if self.edit_callback:
            self.view.edit_button.setHidden(True)
        if self.remove_callback:
            self.view.remove_button.setHidden(True)
        return super().leaveEvent(event)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.view.title_widget.setFixedWidth(int(event.size().width() // 1.5))
        return super().resizeEvent(event)
