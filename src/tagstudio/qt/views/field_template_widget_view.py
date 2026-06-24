# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.enums import Theme
from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.qt.mixed.tag_widget import get_border_color, get_highlight_color, get_text_color
from tagstudio.qt.models.palette import ColorType, UiColor, get_tag_color, get_ui_color

primary_color: QColor = QColor(get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT))
border_color: QColor = get_border_color(primary_color)
highlight_color: QColor = get_highlight_color(primary_color)
text_color: QColor = get_text_color(primary_color, highlight_color)

FIELD_TEMPLATE_BUTTON_STYLESHEET = f"""
    QPushButton{{
        background-color: {Theme.COLOR_BG.value};
        font-weight: 600;
        border-radius: 6px;
        padding-right: 4px;
        padding-left: 4px;
        font-size: 13px;
        text-align: center;
    }}

    QPushButton::hover{{
        background-color: {Theme.COLOR_HOVER.value};
        border-color: {get_ui_color(ColorType.BORDER, UiColor.THEME_DARK)};
        border-style: solid;
        border-width: 2px;
    }}

    QPushButton::pressed{{
        background-color: {Theme.COLOR_PRESSED.value};
        border-color: {get_ui_color(ColorType.LIGHT_ACCENT, UiColor.THEME_DARK)};
        border-style: solid;
        border-width: 2px;
    }}
"""


class FieldTemplateWidgetView(QWidget):
    on_click = Signal()
    on_edit = Signal()
    on_remove = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.__root_layout = QVBoxLayout(self)
        self.__root_layout.setObjectName("root_layout")

        self.__root_layout.setContentsMargins(0, 0, 0, 0)

        # Background button
        self._bg_button = QPushButton(self)
        self.__root_layout.addWidget(self._bg_button)

        self._bg_button.setFlat(True)
        self._bg_button.setMinimumSize(44, 22)
        self._bg_button.setMinimumHeight(22)
        self._bg_button.setMaximumHeight(22)
        self._bg_button.setStyleSheet(FIELD_TEMPLATE_BUTTON_STYLESHEET)

        self.__inner_layout = QHBoxLayout()
        self.__inner_layout.setObjectName("inner_layout")
        self._bg_button.setLayout(self.__inner_layout)

        self.__inner_layout.setContentsMargins(0, 0, 0, 0)

        # Remove button
        self._delete_button = QPushButton(self)
        self._delete_button.setFlat(True)
        self._delete_button.setText("–")
        self._delete_button.setHidden(True)
        self._delete_button.setMinimumSize(22, 22)
        self._delete_button.setMaximumSize(22, 22)

        self.__inner_layout.addWidget(self._delete_button)
        self.__inner_layout.addStretch(1)

        self.__connect_callbacks()

    def __connect_callbacks(self) -> None:
        self._bg_button.clicked.connect(self.on_click.emit)
        self._delete_button.clicked.connect(self.on_remove.emit)
