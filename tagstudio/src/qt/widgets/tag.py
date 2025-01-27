# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from types import FunctionType

import structlog
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QAction, QColor, QEnterEvent, QFontMetrics
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Tag
from src.core.library.alchemy.enums import TagColorEnum
from src.core.palette import ColorType, get_tag_color
from src.qt.translations import Translations

logger = structlog.get_logger(__name__)


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
            f"color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};"
            f"background: {get_tag_color(ColorType.TEXT, TagColorEnum.DEFAULT)};"
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

        # if on_click_callback:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_button = QPushButton(self)
        self.bg_button.setFlat(True)
        self.bg_button.setText(tag.name)
        if has_edit:
            edit_action = QAction(self)
            edit_action.setText(Translations.translate_formatted("generic.edit"))
            edit_action.triggered.connect(on_edit_callback)
            edit_action.triggered.connect(self.on_edit.emit)
            self.bg_button.addAction(edit_action)
        # if on_click_callback:
        self.bg_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        # TODO: This currently doesn't work in "Add Tag" menus. Either fix this or
        # disable it in that context.
        search_for_tag_action = QAction(self)
        search_for_tag_action.setText(Translations.translate_formatted("tag.search_for_tag"))
        search_for_tag_action.triggered.connect(self.on_click.emit)
        self.bg_button.addAction(search_for_tag_action)
        # add_to_search_action = QAction(self)
        # add_to_search_action.setText(Translations.translate_formatted("tag.add_to_search"))
        # self.bg_button.addAction(add_to_search_action)

        self.inner_layout = QHBoxLayout()
        self.inner_layout.setObjectName("innerLayout")
        self.inner_layout.setContentsMargins(2, 2, 2, 2)

        self.bg_button.setLayout(self.inner_layout)
        self.bg_button.setMinimumSize(22, 22)

        primary_color = get_primary_color(tag)
        border_color = (
            get_border_color(primary_color)
            if not (tag.color and tag.color.secondary)
            else (QColor(tag.color.secondary))
        )
        highlight_color = get_highlight_color(
            primary_color
            if not (tag.color and tag.color.secondary)
            else QColor(tag.color.secondary)
        )
        text_color: QColor
        if tag.color and tag.color.secondary:
            text_color = QColor(tag.color.secondary)
        else:
            text_color = get_text_color(primary_color, highlight_color)

        self.bg_button.setStyleSheet(
            f"QPushButton{{"
            f"background: rgba{primary_color.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"font-weight: 600;"
            f"border-color: rgba{border_color.toTuple()};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"padding-right: 4px;"
            f"padding-bottom: 1px;"
            f"padding-left: 4px;"
            f"font-size: 13px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
        )
        self.bg_button.setMinimumHeight(22)
        self.bg_button.setMaximumHeight(22)

        self.base_layout.addWidget(self.bg_button)

        if has_remove:
            self.remove_button = QPushButton(self)
            self.remove_button.setFlat(True)
            self.remove_button.setText("–")
            self.remove_button.setHidden(True)
            self.remove_button.setStyleSheet(
                f"color: rgba{primary_color.toTuple()};"
                f"background: rgba{text_color.toTuple()};"
                f"font-weight: 800;"
                f"border-radius: 3px;"
                f"border-width:0;"
                f"padding-bottom: 4px;"
                f"font-size: 14px"
            )
            self.remove_button.setMinimumSize(18, 18)
            self.remove_button.setMaximumSize(18, 18)
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


def get_primary_color(tag: Tag) -> QColor:
    primary_color = QColor(
        get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)
        if not tag.color
        else tag.color.primary
    )

    return primary_color


def get_border_color(primary_color: QColor) -> QColor:
    border_color: QColor = QColor(primary_color)
    border_color.setRed(min(border_color.red() + 20, 255))
    border_color.setGreen(min(border_color.green() + 20, 255))
    border_color.setBlue(min(border_color.blue() + 20, 255))

    return border_color


def get_highlight_color(primary_color: QColor) -> QColor:
    highlight_color: QColor = QColor(primary_color)
    highlight_color = highlight_color.toHsl()
    highlight_color.setHsl(highlight_color.hue(), min(highlight_color.saturation(), 200), 225, 255)
    highlight_color = highlight_color.toRgb()

    return highlight_color


def get_text_color(primary_color: QColor, highlight_color: QColor) -> QColor:
    if primary_color.lightness() > 120:
        text_color = QColor(primary_color)
        text_color = text_color.toHsl()
        text_color.setHsl(text_color.hue(), text_color.saturation(), 50, 255)
        return text_color.toRgb()
    else:
        return highlight_color
