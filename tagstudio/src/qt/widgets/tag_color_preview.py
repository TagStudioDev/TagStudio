# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Tag
from src.core.library.alchemy.enums import TagColorEnum
from src.core.palette import ColorType, get_tag_color

logger = structlog.get_logger(__name__)


class TagColorPreview(QWidget):
    on_click = Signal()

    def __init__(
        self,
        tag: Tag | None,
    ) -> None:
        super().__init__()
        self.tag = tag

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_button = QPushButton(self)
        self.bg_button.setFlat(True)
        self.bg_button.setMinimumSize(56, 28)
        self.bg_button.setMaximumHeight(28)
        self.bg_button.clicked.connect(self.on_click.emit)

        self.base_layout.addWidget(self.bg_button)

        self.set_tag(tag)

    def set_tag(self, tag: Tag | None):
        self.tag = tag

        try:
            if tag and tag.color:
                self.bg_button.setText(tag.color.name)
            else:
                self.bg_button.setText("None")
        except Exception as e:
            # TODO: Investigate why this happens during tests
            logger.error("[TagColorPreview] Could not access Tag member attributes", error=e)
            self.bg_button.setText("Default Color")
            return

        if not tag:
            return

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
            f"padding-right: 8px;"
            f"padding-bottom: 1px;"
            f"padding-left: 8px;"
            f"font-size: 14px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
        )
        self.bg_button.setMaximumWidth(self.bg_button.sizeHint().width())


def get_primary_color(tag: Tag) -> QColor:
    try:
        primary_color = QColor(
            get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)
            if not tag.color
            else tag.color.primary
        )

        return primary_color
    except Exception as e:
        # TODO: Investigate why this happens during tests
        logger.error("[TagColorPreview] Could not access Tag member attributes", error=e)
        return QColor()


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
