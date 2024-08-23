# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
from types import FunctionType
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QEnterEvent, QAction
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from src.core.library import Library, Tag
from src.core.palette import ColorType, get_tag_color


ERROR = "[ERROR]"
WARNING = "[WARNING]"
INFO = "[INFO]"


class TagWidget(QWidget):
    edit_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[3] / "resources/qt/images/edit_icon_128.png")
    ).resize((math.floor(14 * 1.25), math.floor(14 * 1.25)))
    edit_icon_128.load()
    on_remove = Signal()
    on_click = Signal()
    on_edit = Signal()

    def __init__(
        self,
        library: Library,
        tag: Tag,
        has_edit: bool,
        has_remove: bool,
        on_remove_callback: FunctionType = None,
        on_click_callback: FunctionType = None,
        on_edit_callback: FunctionType = None,
    ) -> None:
        super().__init__()
        self.lib = library
        self.tag = tag
        self.has_edit: bool = has_edit
        self.has_remove: bool = has_remove
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_button = QPushButton(self)
        self.bg_button.setFlat(True)
        self.bg_button.setText(tag.display_name(self.lib).replace("&", "&&"))
        if has_edit:
            edit_action = QAction("Edit", self)
            edit_action.triggered.connect(on_edit_callback)
            edit_action.triggered.connect(self.on_edit.emit)
            self.bg_button.addAction(edit_action)
        self.bg_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        search_for_tag_action = QAction("Search for Tag", self)

        search_for_tag_action.triggered.connect(self.on_click.emit)
        self.bg_button.addAction(search_for_tag_action)
        add_to_search_action = QAction("Add to Search", self)
        self.bg_button.addAction(add_to_search_action)

        self.inner_layout = QHBoxLayout()
        self.inner_layout.setObjectName("innerLayout")
        self.inner_layout.setContentsMargins(2, 2, 2, 2)

        self.bg_button.setLayout(self.inner_layout)
        self.bg_button.setMinimumSize(math.ceil(22 * 1.5), 22)
        self.bg_button.setStyleSheet(
            f"""QPushButton{{
            background: {get_tag_color(ColorType.PRIMARY, tag.color)};
            color: {get_tag_color(ColorType.TEXT, tag.color)};
            font-weight: 600;
            border-color:{get_tag_color(ColorType.BORDER, tag.color)};
            border-radius: 6px;
            border-style:solid;
            border-width: {math.ceil(1*self.devicePixelRatio())}px;
            padding-right: 4px;
            padding-bottom: 1px;
            padding-left: 4px;
            font-size: 13px
            }}
            QPushButton::hover{{
            border-color:{get_tag_color(ColorType.LIGHT_ACCENT, tag.color)};
            }}
            """
        )

        self.base_layout.addWidget(self.bg_button)

        if has_remove:
            self.remove_button = QPushButton(self)
            self.remove_button.setFlat(True)
            self.remove_button.setText("–")
            self.remove_button.setHidden(True)
            self.remove_button.setStyleSheet(
                f"""color: {get_tag_color(ColorType.PRIMARY, tag.color)};
                background: {get_tag_color(ColorType.TEXT, tag.color)};
                font-weight: 800;
                border-radius: 4px;
                border-width:0;
                padding-bottom: 4px;
                font-size: 14px
                """
            )
            self.remove_button.setMinimumSize(19, 19)
            self.remove_button.setMaximumSize(19, 19)
            self.remove_button.clicked.connect(self.on_remove.emit)

        if has_remove:
            self.inner_layout.addWidget(self.remove_button)
        self.inner_layout.addStretch(1)

        # NOTE: Do this if you don't want the tag to stretch, like in a search.
        # self.bg_button.setMaximumWidth(self.bg_button.sizeHint().width())

        self.bg_button.clicked.connect(self.on_click.emit)

    def enterEvent(self, event: QEnterEvent) -> None:
        if self.has_remove:
            self.remove_button.setHidden(False)
        self.update()
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self.has_remove:
            self.remove_button.setHidden(True)
        self.update()
        return super().leaveEvent(event)
