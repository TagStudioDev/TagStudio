# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

import structlog
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QAction, QColor, QEnterEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.library.alchemy.models import TagColorGroup
from src.qt.helpers.escape_text import escape_text
from src.qt.translations import Translations
from src.qt.widgets.tag import (
    get_border_color,
    get_highlight_color,
    get_text_color,
)

logger = structlog.get_logger(__name__)

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.core.library.alchemy import Library


class TagColorLabel(QWidget):
    """A widget for displaying a tag color's name.

    Not to be confused with a tag color swatch widget.
    """

    on_remove = Signal()
    on_click = Signal()

    def __init__(
        self,
        color: TagColorGroup | None,
        has_edit: bool,
        has_remove: bool,
        library: "Library | None" = None,
    ) -> None:
        super().__init__()
        self.color = color
        self.lib: Library | None = library
        self.has_edit = has_edit
        self.has_remove = has_remove

        self.base_layout = QVBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_button = QPushButton(self)
        self.bg_button.setFlat(True)

        edit_action = QAction(self)
        edit_action.setText(Translations["generic.edit"])
        edit_action.triggered.connect(self.on_click.emit)
        self.bg_button.addAction(edit_action)
        self.bg_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        if has_edit:
            self.bg_button.clicked.connect(self.on_click.emit)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            edit_action.setEnabled(False)

        self.inner_layout = QHBoxLayout()
        self.inner_layout.setObjectName("innerLayout")
        self.inner_layout.setContentsMargins(0, 0, 0, 0)

        self.remove_button = QPushButton(self)
        self.remove_button.setFlat(True)
        self.remove_button.setText("–")
        self.remove_button.setHidden(True)
        self.remove_button.setMinimumSize(22, 22)
        self.remove_button.setMaximumSize(22, 22)
        self.inner_layout.addWidget(self.remove_button)
        self.inner_layout.addStretch(1)
        if self.has_remove:
            self.remove_button.clicked.connect(self.on_remove.emit)
        else:
            self.remove_button.setHidden(True)

        self.bg_button.setLayout(self.inner_layout)
        self.bg_button.setMinimumSize(44, 22)
        self.bg_button.setMaximumHeight(22)

        self.base_layout.addWidget(self.bg_button)

        # NOTE: Do this if you don't want the tag to stretch, like in a search.
        # self.bg_button.setMaximumWidth(self.bg_button.sizeHint().width())

        self.set_color(color)

    def set_color(self, color: TagColorGroup | None) -> None:
        self.color = color

        if not color:
            return

        primary_color = self._get_primary_color(color)
        border_color = (
            get_border_color(primary_color)
            if not (color and color.secondary and color.color_border)
            else (QColor(color.secondary))
        )
        highlight_color = get_highlight_color(
            primary_color if not (color and color.secondary) else QColor(color.secondary)
        )
        text_color: QColor
        if color and color.secondary:
            text_color = QColor(color.secondary)
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
            f"padding-left: 4px;"
            f"font-size: 13px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
            f"QPushButton::pressed{{"
            f"background: rgba{highlight_color.toTuple()};"
            f"color: rgba{primary_color.toTuple()};"
            f"border-color: rgba{primary_color.toTuple()};"
            f"}}"
            f"QPushButton::focus{{"
            f"padding-right: 0px;"
            f"padding-left: 0px;"
            f"outline-style: solid;"
            f"outline-width: 1px;"
            f"outline-radius: 4px;"
            f"outline-color: rgba{text_color.toTuple()};"
            f"}}"
        )

        self.remove_button.setStyleSheet(
            f"QPushButton{{"
            f"color: rgba{primary_color.toTuple()};"
            f"background: rgba{text_color.toTuple()};"
            f"font-weight: 800;"
            f"border-radius: 5px;"
            f"border-width: 4;"
            f"border-color: rgba(0,0,0,0);"
            f"padding-bottom: 4px;"
            f"font-size: 14px"
            f"}}"
            f"QPushButton::hover{{"
            f"background: rgba{primary_color.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"border-width: 2;"
            f"border-radius: 6px;"
            f"}}"
            f"QPushButton::pressed{{"
            f"background: rgba{border_color.toTuple()};"
            f"color: rgba{highlight_color.toTuple()};"
            f"}}"
            f"QPushButton::focus{{"
            f"background: rgba{border_color.toTuple()};"
            f"outline:none;"
            f"}}"
        )

        self.bg_button.setText(escape_text(color.name))

    def _get_primary_color(self, color: TagColorGroup) -> QColor:
        primary_color = QColor(color.primary)

        return primary_color

    def set_has_remove(self, has_remove: bool):
        self.has_remove = has_remove

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
