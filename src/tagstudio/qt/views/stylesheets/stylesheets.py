# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from PySide6.QtGui import QColor

from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.qt.mixed.tag_widget import get_border_color, get_highlight_color, get_text_color
from tagstudio.qt.models.palette import ColorType, get_tag_color


def checkbox_style() -> str:
    primary_color = QColor(get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT))
    border_color = get_border_color(primary_color)
    highlight_color = get_highlight_color(primary_color)
    text_color: QColor = get_text_color(primary_color, highlight_color)
    return (
        f"QCheckBox{{"
        f"background: rgba{primary_color.toTuple()};"
        f"color: rgba{text_color.toTuple()};"
        f"border-color: rgba{border_color.toTuple()};"
        f"border-radius: 6px;"
        f"border-style:solid;"
        f"border-width: 2px;"
        f"}}"
        f"QCheckBox::indicator{{"
        f"width: 10px;"
        f"height: 10px;"
        f"border-radius: 2px;"
        f"margin: 4px;"
        f"}}"
        f"QCheckBox::indicator:checked{{"
        f"background: rgba{text_color.toTuple()};"
        f"}}"
        f"QCheckBox::hover{{"
        f"border-color: rgba{highlight_color.toTuple()};"
        f"}}"
        f"QCheckBox::focus{{"
        f"border-color: rgba{highlight_color.toTuple()};"
        f"outline:none;"
        f"}}"
    )
