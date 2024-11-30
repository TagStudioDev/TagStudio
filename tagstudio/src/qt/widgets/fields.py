# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
from pathlib import Path
from types import MethodType
from typing import Callable, Optional

from PIL import Image, ImageQt
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper


class FieldContainer(QWidget):
    # TODO: reference a resources folder rather than path.parents[3]?
    clipboard_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[3] / "resources/qt/images/clipboard_icon_128.png")
    ).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
    clipboard_icon_128.load()

    edit_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[3] / "resources/qt/images/edit_icon_128.png")
    ).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
    edit_icon_128.load()

    trash_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[3] / "resources/qt/images/trash_icon_128.png")
    ).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
    trash_icon_128.load()

    def __init__(self, title: str = "Field", inline: bool = True) -> None:
        super().__init__()
        self.setObjectName("fieldContainer")
        self.title: str = title
        self.inline: bool = inline
        self.copy_callback: Callable = None
        self.edit_callback: Callable = None
        self.remove_callback: Callable = None
        button_size = 24

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setObjectName("baseLayout")
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.inner_layout = QVBoxLayout()
        self.inner_layout.setObjectName("innerLayout")
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(0)
        self.inner_container = QWidget()
        self.inner_container.setObjectName("innerContainer")
        self.inner_container.setLayout(self.inner_layout)
        self.root_layout.addWidget(self.inner_container)

        self.title_container = QWidget()
        self.title_layout = QHBoxLayout(self.title_container)
        self.title_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.title_layout.setObjectName("fieldLayout")
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_layout.setSpacing(0)
        self.inner_layout.addWidget(self.title_container)

        self.title_widget = QLabel()
        self.title_widget.setMinimumHeight(button_size)
        self.title_widget.setObjectName("fieldTitle")
        self.title_widget.setWordWrap(True)
        self.title_widget.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.title_widget.setText(title)
        self.title_layout.addWidget(self.title_widget)
        self.title_layout.addStretch(2)

        self.copy_button = QPushButtonWrapper()
        self.copy_button.setMinimumSize(button_size, button_size)
        self.copy_button.setMaximumSize(button_size, button_size)
        self.copy_button.setFlat(True)
        self.copy_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.clipboard_icon_128)))
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_layout.addWidget(self.copy_button)
        self.copy_button.setHidden(True)

        self.edit_button = QPushButtonWrapper()
        self.edit_button.setMinimumSize(button_size, button_size)
        self.edit_button.setMaximumSize(button_size, button_size)
        self.edit_button.setFlat(True)
        self.edit_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.edit_icon_128)))
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_layout.addWidget(self.edit_button)
        self.edit_button.setHidden(True)

        self.remove_button = QPushButtonWrapper()
        self.remove_button.setMinimumSize(button_size, button_size)
        self.remove_button.setMaximumSize(button_size, button_size)
        self.remove_button.setFlat(True)
        self.remove_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.trash_icon_128)))
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_layout.addWidget(self.remove_button)
        self.remove_button.setHidden(True)

        self.field_container = QWidget()
        self.field_container.setObjectName("fieldContainer")
        self.field_layout = QHBoxLayout()
        self.field_layout.setObjectName("fieldLayout")
        self.field_layout.setContentsMargins(0, 0, 0, 0)
        self.field_container.setLayout(self.field_layout)
        self.inner_layout.addWidget(self.field_container)

    def set_copy_callback(self, callback: Optional[MethodType]):
        if self.copy_button.is_connected:
            self.copy_button.clicked.disconnect()

        self.copy_callback = callback
        self.copy_button.clicked.connect(callback)
        if callback is not None:
            self.copy_button.is_connected = True

    def set_edit_callback(self, callback: Callable):
        if self.edit_button.is_connected:
            self.edit_button.clicked.disconnect()

        self.edit_callback = callback
        self.edit_button.clicked.connect(callback)
        if callback is not None:
            self.edit_button.is_connected = True

    def set_remove_callback(self, callback: Callable):
        if self.remove_button.is_connected:
            self.remove_button.clicked.disconnect()

        self.remove_callback = callback
        self.remove_button.clicked.connect(callback)
        self.remove_button.is_connected = True

    def set_inner_widget(self, widget: "FieldWidget"):
        if self.field_layout.itemAt(0):
            old: QWidget = self.field_layout.itemAt(0).widget()
            self.field_layout.removeWidget(old)
            old.deleteLater()

        self.field_layout.addWidget(widget)

    def get_inner_widget(self):
        if self.field_layout.itemAt(0):
            return self.field_layout.itemAt(0).widget()
        return None

    def set_title(self, title: str):
        self.title = title
        self.title_widget.setText(title)

    def set_inline(self, inline: bool):
        self.inline = inline

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        # NOTE: You could pass the hover event to the FieldWidget if needed.
        if self.copy_callback:
            self.copy_button.setHidden(False)
        if self.edit_callback:
            self.edit_button.setHidden(False)
        if self.remove_callback:
            self.remove_button.setHidden(False)
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        if self.copy_callback:
            self.copy_button.setHidden(True)
        if self.edit_callback:
            self.edit_button.setHidden(True)
        if self.remove_callback:
            self.remove_button.setHidden(True)
        return super().leaveEvent(event)


class FieldWidget(QWidget):
    def __init__(self, title) -> None:
        super().__init__()
        self.title = title
