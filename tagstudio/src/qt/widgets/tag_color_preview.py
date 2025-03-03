# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.library.alchemy.enums import TagColorEnum
from src.core.library.alchemy.models import TagColorGroup
from src.core.palette import ColorType, get_tag_color
from src.qt.translations import Translations
from src.qt.widgets.tag import (
    get_border_color,
    get_highlight_color,
    get_text_color,
)

if typing.TYPE_CHECKING:
    from src.core.library import Library

logger = structlog.get_logger(__name__)


class TagColorPreview(QWidget):
    on_click = Signal()

    def __init__(
        self,
        library: "Library",
        tag_color_group: TagColorGroup | None,
    ) -> None:
        super().__init__()
        self.lib: Library = library
        self.tag_color_group = tag_color_group

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        self.button = QPushButton(self)
        self.button.setFlat(True)
        self.button.setMinimumSize(56, 28)
        self.button.setMaximumHeight(28)
        self.button.clicked.connect(self.on_click.emit)

        self.base_layout.addWidget(self.button)

        self.set_tag_color_group(tag_color_group)

    def set_tag_color_group(self, color_group: TagColorGroup | None):
        logger.info(
            "[TagColorPreview] Setting tag color",
            primary=color_group.primary if color_group else None,
            secondary=color_group.secondary if color_group else None,
        )
        self.tag_color_group = color_group

        if color_group:
            self.button.setText(color_group.name)
            self.button.setText(
                f"{color_group.name} ({self.lib.get_namespace_name(color_group.namespace)})"
            )
        else:
            self.button.setText(Translations["color.title.no_color"])

        primary_color = self._get_primary_color(color_group)
        border_color = (
            get_border_color(primary_color)
            if not (color_group and color_group.secondary and color_group.color_border)
            else (QColor(color_group.secondary))
        )
        highlight_color = get_highlight_color(
            primary_color
            if not (color_group and color_group.secondary)
            else QColor(color_group.secondary)
        )
        text_color: QColor
        if color_group and color_group.secondary:
            text_color = QColor(color_group.secondary)
        else:
            text_color = get_text_color(primary_color, highlight_color)

        self.button.setStyleSheet(
            f"QPushButton{{"
            f"background: rgba{primary_color.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"font-weight: 600;"
            f"border-color: rgba{border_color.toTuple()};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"padding-right: 8px;"
            f"padding-left: 8px;"
            f"font-size: 14px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
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
        # Add back the padding if the hint is generated while the button has focus (no padding)
        self.button.setMinimumWidth(
            self.button.sizeHint().width() + (16 if self.button.hasFocus() else 0)
        )

    def _get_primary_color(self, tag_color_group: TagColorGroup | None) -> QColor:
        primary_color = QColor(
            get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)
            if not tag_color_group
            else tag_color_group.primary
        )

        return primary_color
