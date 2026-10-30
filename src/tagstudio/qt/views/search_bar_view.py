# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import QSize, QStringListModel, Qt
from PySide6.QtWidgets import QCompleter, QHBoxLayout, QLayout, QLineEdit, QPushButton

from tagstudio.i18n.translations import Translations
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import image_theme_color_overlay
from tagstudio.qt.views.styles.stylesheets import MED_HEIGHT, RADIUS, WIN_PAD
from tagstudio.qt.views.styles.tagstudio_style import set_joined_edges


class SearchBarView(QHBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setContentsMargins(WIN_PAD, 0, 0, 0)
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(0)
        self.back_button = QPushButton()
        self.back_button.setProperty("radius", RADIUS)
        self.back_button.setObjectName("back_button")
        self.back_button.setFixedSize(QSize(MED_HEIGHT, MED_HEIGHT))
        set_joined_edges(self.back_button, Qt.Edge.RightEdge)
        nav_layout.addWidget(self.back_button)

        self.forward_button = QPushButton()
        self.forward_button.setProperty("radius", RADIUS)
        self.forward_button.setObjectName("forward_button")
        self.forward_button.setFixedSize(QSize(MED_HEIGHT, MED_HEIGHT))
        set_joined_edges(self.forward_button, Qt.Edge.LeftEdge)
        nav_layout.addWidget(self.forward_button)
        self.addLayout(nav_layout)
        self.set_button_icons()

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(Translations["home.search_entries"])
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumSize(QSize(0, MED_HEIGHT))
        self.search_field_completion_list = QStringListModel()
        self.search_field_completer = QCompleter(
            self.search_field_completion_list, self.search_field
        )
        self.search_field_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_field.setCompleter(self.search_field_completer)
        self.addWidget(self.search_field)

        self.search_button = QPushButton(Translations["home.search"])
        self.search_button.setProperty("radius", RADIUS)
        self.search_button.setObjectName("search_button")
        self.search_button.setMinimumSize(QSize(0, MED_HEIGHT))
        self.addWidget(self.search_button)

    def set_button_icons(self) -> None:
        """Color the navigation buttons' icons for the current theme."""
        rm = ResourceManager()
        self.back_button.setIcon(image_theme_color_overlay(rm.bxs_left_arrow, use_alpha=False))
        self.forward_button.setIcon(image_theme_color_overlay(rm.bxs_right_arrow, use_alpha=False))
