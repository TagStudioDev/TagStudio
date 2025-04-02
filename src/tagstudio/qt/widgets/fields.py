# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
from collections.abc import Callable
from pathlib import Path
from typing import override
from warnings import catch_warnings

import structlog
from PIL import Image, ImageQt
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.enums import Theme

logger = structlog.get_logger(__name__)


class FieldContainer(QWidget):
    # TODO: reference a resources folder rather than path.parents[2]?
    clipboard_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[2] / "resources/qt/images/clipboard_icon_128.png")
    ).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
    clipboard_icon_128.load()

    edit_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[2] / "resources/qt/images/edit_icon_128.png")
    ).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
    edit_icon_128.load()

    trash_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[2] / "resources/qt/images/trash_icon_128.png")
    ).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
    trash_icon_128.load()

    # TODO: There should be a global button theme somewhere.
    container_style = (
        f"QWidget#fieldContainer{{"
        "border-radius:4px;"
        f"}}"
        f"QWidget#fieldContainer::hover{{"
        f"background-color:{Theme.COLOR_HOVER.value};"
        f"}}"
        f"QWidget#fieldContainer::pressed{{"
        f"background-color:{Theme.COLOR_PRESSED.value};"
        f"}}"
    )

    def __init__(self, title: str = "Field", inline: bool = True) -> None:
        super().__init__()
        self.setObjectName("fieldContainer")
        self.title: str = title
        self.inline: bool = inline
        self.copy_callback: Callable[[], None] | None = None
        self.edit_callback: Callable[[], None] | None = None
        self.remove_callback: Callable[[], None] | None = None
        button_size = 24

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setObjectName("baseLayout")
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.inner_layout = QVBoxLayout()
        self.inner_layout.setObjectName("innerLayout")
        self.inner_layout.setContentsMargins(6, 0, 6, 6)
        self.inner_layout.setSpacing(0)
        self.field_container = QWidget()
        self.field_container.setObjectName("fieldContainer")
        self.field_container.setLayout(self.inner_layout)
        self.root_layout.addWidget(self.field_container)

        self.title_container = QWidget()
        self.title_layout = QHBoxLayout(self.title_container)
        self.title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.title_layout.setObjectName("fieldLayout")
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_layout.setSpacing(0)
        self.inner_layout.addWidget(self.title_container)

        self.title_widget = QLabel()
        self.title_widget.setMinimumHeight(button_size)
        self.title_widget.setObjectName("fieldTitle")
        self.title_widget.setWordWrap(True)
        self.title_widget.setText(title)
        self.title_layout.addWidget(self.title_widget)
        self.title_layout.addStretch(2)

        self.copy_button = QPushButton()
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setMinimumSize(button_size, button_size)
        self.copy_button.setMaximumSize(button_size, button_size)
        self.copy_button.setFlat(True)
        self.copy_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.clipboard_icon_128)))
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_layout.addWidget(self.copy_button)
        self.copy_button.setHidden(True)

        self.edit_button = QPushButton()
        self.edit_button.setObjectName("editButton")
        self.edit_button.setMinimumSize(button_size, button_size)
        self.edit_button.setMaximumSize(button_size, button_size)
        self.edit_button.setFlat(True)
        self.edit_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.edit_icon_128)))
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_layout.addWidget(self.edit_button)
        self.edit_button.setHidden(True)

        self.remove_button = QPushButton()
        self.remove_button.setObjectName("removeButton")
        self.remove_button.setMinimumSize(button_size, button_size)
        self.remove_button.setMaximumSize(button_size, button_size)
        self.remove_button.setFlat(True)
        self.remove_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.trash_icon_128)))
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_layout.addWidget(self.remove_button)
        self.remove_button.setHidden(True)

        self.field = QWidget()
        self.field.setObjectName("field")
        self.field_layout = QHBoxLayout()
        self.field_layout.setObjectName("fieldLayout")
        self.field_layout.setContentsMargins(0, 0, 0, 0)
        self.field.setLayout(self.field_layout)
        self.inner_layout.addWidget(self.field)

        self.set_title(title)
        self.setStyleSheet(FieldContainer.container_style)

    def set_copy_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.copy_button.clicked.disconnect()

        self.copy_callback = callback
        if callback:
            self.copy_button.clicked.connect(callback)

    def set_edit_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.edit_button.clicked.disconnect()

        self.edit_callback = callback
        if callback:
            self.edit_button.clicked.connect(callback)

    def set_remove_callback(self, callback: Callable[[], None] | None = None) -> None:
        with catch_warnings(record=True):
            self.remove_button.clicked.disconnect()

        self.remove_callback = callback
        if callback:
            self.remove_button.clicked.connect(callback)

    def set_inner_widget(self, widget: "FieldWidget") -> None:
        if self.field_layout.itemAt(0):
            old: QWidget = self.field_layout.itemAt(0).widget()
            self.field_layout.removeWidget(old)
            old.deleteLater()

        self.field_layout.addWidget(widget)

    def get_inner_widget(self) -> QWidget | None:
        if self.field_layout.itemAt(0):
            return self.field_layout.itemAt(0).widget()
        return None

    def set_title(self, title: str) -> None:
        self.title = self.title = f"<h4>{title}</h4>"
        self.title_widget.setText(self.title)

    def set_inline(self, inline: bool) -> None:
        self.inline = inline

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        # NOTE: You could pass the hover event to the FieldWidget if needed.
        if self.copy_callback:
            self.copy_button.setHidden(False)
        if self.edit_callback:
            self.edit_button.setHidden(False)
        if self.remove_callback:
            self.remove_button.setHidden(False)
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        if self.copy_callback:
            self.copy_button.setHidden(True)
        if self.edit_callback:
            self.edit_button.setHidden(True)
        if self.remove_callback:
            self.remove_button.setHidden(True)
        return super().leaveEvent(event)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.title_widget.setFixedWidth(int(event.size().width() // 1.5))
        return super().resizeEvent(event)


class FieldWidget(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.title: str = title
