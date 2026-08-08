# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.qt.models.palette import ColorType, get_tag_color
from tagstudio.qt.views.stylesheets.stylesheets import (
    get_tag_border_color,
    get_tag_highlight_color,
    get_tag_text_color,
    list_button_style,
    tag_remove_button_style,
)

# TODO: These colors and logic should be moved to and reworked in the stylesheets file.
primary_color: QColor = QColor(get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT))
border_color: QColor = get_tag_border_color(primary_color)
highlight_color: QColor = get_tag_highlight_color(primary_color)
text_color: QColor = get_tag_text_color(primary_color, highlight_color)


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
        self._bg_button.setStyleSheet(list_button_style())

        self.__inner_layout = QHBoxLayout()
        self.__inner_layout.setObjectName("inner_layout")
        self._bg_button.setLayout(self.__inner_layout)

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.__inner_layout.setContentsMargins(0, 0, 0, 0)

        # Remove button
        self._delete_button = QPushButton(self)
        self._delete_button.setFlat(True)
        self._delete_button.setText("–")
        self._delete_button.setHidden(True)
        self._delete_button.setMinimumSize(22, 22)
        self._delete_button.setMaximumSize(22, 22)
        self._delete_button.setStyleSheet(
            tag_remove_button_style(primary_color, text_color, border_color, highlight_color)
        )

        self.__inner_layout.addWidget(self._delete_button)
        self.__inner_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.__connect_callbacks()

    def __connect_callbacks(self) -> None:
        self._bg_button.clicked.connect(self.on_click.emit)
        self._delete_button.clicked.connect(self.on_remove.emit)
