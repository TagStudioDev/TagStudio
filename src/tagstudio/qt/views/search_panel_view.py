# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tagstudio.qt.translations import Translations
from tagstudio.qt.views.stylesheets.stylesheets import list_button_style

if TYPE_CHECKING:
    pass


class SearchPanelView(QVBoxLayout):
    def __init__(
        self, placeholder_text: str, create_text: str = "", is_chooser: bool = True
    ) -> None:
        self.is_chooser: bool = is_chooser
        super().__init__()
        self.setContentsMargins(6, 0, 6, 0)

        # Limit container
        self.limit_container = QWidget()
        self.limit_layout = QHBoxLayout(self.limit_container)
        self.limit_layout.setContentsMargins(0, 0, 0, 0)
        self.limit_layout.setSpacing(12)
        self.limit_layout.addStretch(1)
        self.limit_title = QLabel(Translations["home.search.view_limit"])
        self.limit_layout.addWidget(self.limit_title)
        self.addWidget(self.limit_container)

        # Limit dropdown
        self.limit_combobox = QComboBox()
        self.limit_layout.addWidget(self.limit_combobox)
        self.limit_layout.addStretch(1)
        self.limit_combobox.setEditable(False)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(placeholder_text)
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.addWidget(self.search_field)

        # Scroll area
        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_contents)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.addWidget(self.scroll_area)

        # Create button
        self.create_button = QPushButton(create_text)
        if not self.is_chooser:
            self.addWidget(self.create_button)

        # Create and add button
        self.create_and_add_button_in_layout: bool = False
        self.create_and_add_button = QPushButton()
        self.create_and_add_button.setFlat(True)
        self.create_and_add_button.setMinimumSize(22, 22)
        self.create_and_add_button.setStyleSheet(list_button_style(border_style="dashed"))
