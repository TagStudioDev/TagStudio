# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from typing import TYPE_CHECKING, override

import structlog
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QAction, QColor, QEnterEvent, QFontMetrics
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.helpers.escape_text import escape_text
from tagstudio.qt.models.palette import ColorType, get_tag_color
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.stylesheets.stylesheets import (
    get_tag_border_color,
    get_tag_highlight_color,
    get_tag_primary_color,
    get_tag_text_color,
    tag_remove_button_style,
    tag_style,
)

logger = structlog.get_logger(__name__)

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library


class TagAliasWidget(QWidget):
    on_remove = Signal()

    def __init__(
        self,
        id: int | None = 0,
        alias: str | None = None,
        on_remove_callback: Callable[[], None] | None = None,
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

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self.update()
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self.update()
        return super().leaveEvent(event)


class TagWidget(QWidget):
    on_remove = Signal()
    on_click = Signal()
    on_edit = Signal()

    tag: Tag | None

    def __init__(
        self,
        tag: Tag | None,
        has_edit: bool,
        has_remove: bool,
        library: "Library | None" = None,
        on_remove_callback: Callable[[], None] | None = None,
        on_click_callback: Callable[[], None] | None = None,
        on_edit_callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self.tag = tag
        self.lib: Library | None = library
        self.has_edit = has_edit
        self.has_remove = has_remove

        # if on_click_callback:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_button = QPushButton(self)
        self.bg_button.setFlat(True)

        # add callbacks
        if on_remove_callback is not None:
            self.on_remove.connect(on_remove_callback)
        if on_click_callback is not None:
            self.on_click.connect(on_click_callback)
        if on_edit_callback is not None:
            self.on_edit.connect(on_edit_callback)

        # add edit action
        if has_edit:
            edit_action = QAction(self)
            edit_action.setText(Translations["generic.edit"])
            edit_action.triggered.connect(self.on_edit.emit)
            self.bg_button.addAction(edit_action)
        # if on_click_callback:
        self.bg_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        # TODO: This currently doesn't work in "Add Tag" menus. Either fix this or
        # disable it in that context.
        self.search_for_tag_action = QAction(self)
        self.search_for_tag_action.setText(Translations["tag.search_for_tag"])
        self.bg_button.addAction(self.search_for_tag_action)
        # add_to_search_action = QAction(self)
        # add_to_search_action.setText(Translations.translate_formatted("tag.add_to_search"))
        # self.bg_button.addAction(add_to_search_action)

        self.inner_layout = QHBoxLayout()
        self.inner_layout.setObjectName("innerLayout")
        self.inner_layout.setContentsMargins(0, 0, 0, 0)

        self._delete_button = QPushButton(self)
        self._delete_button.setFlat(True)
        self._delete_button.setText("–")
        self._delete_button.setHidden(True)
        self._delete_button.setMinimumSize(22, 22)
        self._delete_button.setMaximumSize(22, 22)
        self._delete_button.clicked.connect(self.on_remove.emit)
        self._delete_button.setHidden(True)
        self.inner_layout.addWidget(self._delete_button)
        self.inner_layout.addStretch(1)

        self.bg_button.setLayout(self.inner_layout)
        self.bg_button.setMinimumSize(44, 22)

        self.bg_button.setMinimumHeight(22)
        self.bg_button.setMaximumHeight(22)

        self.base_layout.addWidget(self.bg_button)

        # NOTE: Do this if you don't want the tag to stretch, like in a search.
        # self.bg_button.setMaximumWidth(self.bg_button.sizeHint().width())

        self.bg_button.clicked.connect(self.on_click.emit)

        self.set_tag(tag)

    def set_tag(self, tag: Tag | None) -> None:
        self.tag = tag

        if not tag:
            return

        primary_color = get_tag_primary_color(tag)
        border_color = (
            get_tag_border_color(primary_color)
            if not (tag.color and tag.color.secondary and tag.color.color_border)
            else (QColor(tag.color.secondary))
        )
        highlight_color = get_tag_highlight_color(
            primary_color
            if not (tag.color and tag.color.secondary)
            else QColor(tag.color.secondary)
        )
        text_color: QColor
        if tag.color and tag.color.secondary:
            text_color = QColor(tag.color.secondary)
        else:
            text_color = get_tag_text_color(primary_color, highlight_color)

        self.bg_button.setStyleSheet(
            tag_style(primary_color, text_color, border_color, highlight_color)
        )

        self._delete_button.setStyleSheet(
            tag_remove_button_style(primary_color, text_color, border_color, highlight_color)
        )

        if self.lib:
            self.bg_button.setText(escape_text(self.lib.tag_display_name(tag)))
        else:
            self.bg_button.setText(escape_text(tag.name))

    def set_has_remove(self, has_remove: bool):
        self.has_remove = has_remove

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        if self.has_remove:
            self._delete_button.setHidden(False)
        self.update()
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        if self.has_remove:
            self._delete_button.setHidden(True)
        self.update()
        return super().leaveEvent(event)
