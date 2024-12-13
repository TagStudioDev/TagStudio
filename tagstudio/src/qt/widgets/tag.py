# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
from pathlib import Path
from types import FunctionType

from PIL import Image
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QAction, QEnterEvent, QFontMetrics
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Tag
from src.core.library.alchemy.enums import TagColor
from src.core.palette import ColorType, get_tag_color


class TagAliasWidget(QWidget):
    on_remove = Signal()

    def __init__(
        self,
        id: int | None = 0,
        alias: str | None = None,
        on_remove_callback=None,
    ) -> None:
        super().__init__()

        self.id = id

        # if on_click_callback:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.base_layout = QHBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        self.on_remove.connect(on_remove_callback)

        self.text_field = QLineEdit(self)
        self.text_field.textChanged.connect(self._adjust_width)

        if alias is not None:
            self.text_field.setText(alias)
        else:
            self.text_field.setText("")

        self._adjust_width()

        self.remove_button = QPushButton(self)
        self.remove_button.setFlat(True)
        self.remove_button.setText("–")
        self.remove_button.setHidden(False)
        self.remove_button.setStyleSheet(
            f"color: {get_tag_color(ColorType.PRIMARY, TagColor.DEFAULT)};"
            f"background: {get_tag_color(ColorType.TEXT, TagColor.DEFAULT)};"
            f"font-weight: 800;"
            f"border-radius: 4px;"
            f"border-width:0;"
            f"padding-bottom: 4px;"
            f"font-size: 14px"
        )
        self.remove_button.setMinimumSize(19, 19)
        self.remove_button.setMaximumSize(19, 19)
        self.remove_button.clicked.connect(self.on_remove.emit)

        self.base_layout.addWidget(self.remove_button)
        self.base_layout.addWidget(self.text_field)

    def _adjust_width(self):
        text = self.text_field.text() or self.text_field.placeholderText()
        font_metrics = QFontMetrics(self.text_field.font())
        text_width = font_metrics.horizontalAdvance(text) + 10  # Add padding

        # Set the minimum width of the QLineEdit
        self.text_field.setMinimumWidth(text_width)
        self.text_field.adjustSize()

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        self.update()
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        self.update()
        return super().leaveEvent(event)


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
        tag: Tag,
        has_edit: bool,
        has_remove: bool,
        on_remove_callback: FunctionType = None,
        on_click_callback: FunctionType = None,
        on_edit_callback: FunctionType = None,
    ) -> None:
        super().__init__()
        self.tag = tag
        self.has_edit = has_edit
        self.has_remove = has_remove
        # self.bg_label = QLabel()
        # self.setStyleSheet('background-color:blue;')

        # if on_click_callback:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_button = QPushButton(self)
        self.bg_button.setFlat(True)
        self.bg_button.setText(tag.name)
        if has_edit:
            edit_action = QAction("Edit", self)
            edit_action.triggered.connect(on_edit_callback)
            edit_action.triggered.connect(self.on_edit.emit)
            self.bg_button.addAction(edit_action)
        # if on_click_callback:
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
            f"QPushButton{{"
            f"background: {get_tag_color(ColorType.PRIMARY, tag.color)};"
            f"color: {get_tag_color(ColorType.TEXT, tag.color)};"
            f"font-weight: 600;"
            f"border-color:{get_tag_color(ColorType.BORDER, tag.color)};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: {math.ceil(self.devicePixelRatio())}px;"
            f"padding-right: 4px;"
            f"padding-bottom: 1px;"
            f"padding-left: 4px;"
            f"font-size: 13px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, tag.color)};"
            f"}}"
        )

        self.base_layout.addWidget(self.bg_button)

        if has_remove:
            self.remove_button = QPushButton(self)
            self.remove_button.setFlat(True)
            self.remove_button.setText("–")
            self.remove_button.setHidden(True)
            self.remove_button.setStyleSheet(
                f"color: {get_tag_color(ColorType.PRIMARY, tag.color)};"
                f"background: {get_tag_color(ColorType.TEXT, tag.color)};"
                f"font-weight: 800;"
                f"border-radius: 4px;"
                f"border-width:0;"
                f"padding-bottom: 4px;"
                f"font-size: 14px"
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

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        if self.has_remove:
            self.remove_button.setHidden(False)
        self.update()
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        if self.has_remove:
            self.remove_button.setHidden(True)
        self.update()
        return super().leaveEvent(event)
