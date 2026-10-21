# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import QSize, QStringListModel, Qt
from PySide6.QtWidgets import QCompleter, QHBoxLayout, QLayout, QLineEdit, QPushButton

from tagstudio.i18n.translations import Translations
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import auto_theme_overlay
from tagstudio.qt.views.styles.stylesheets import WIN_PAD


class SearchBarView(QHBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setContentsMargins(WIN_PAD, 0, 0, 0)
        rm = ResourceManager()

        self.back_button = QPushButton()
        self.back_button.setIcon(auto_theme_overlay(rm.bxs_left_arrow, use_alpha=False))
        self.back_button.setObjectName("back_button")
        self.back_button.setMinimumSize(QSize(32, 32))
        self.back_button.setMaximumSize(QSize(32, 16777215))
        self.addWidget(self.back_button)

        self.forward_button = QPushButton()
        self.forward_button.setIcon(auto_theme_overlay(rm.bxs_right_arrow, use_alpha=False))
        self.forward_button.setIconSize(QSize(16, 16))
        self.forward_button.setObjectName("forward_button")
        self.forward_button.setMinimumSize(QSize(32, 32))
        self.forward_button.setMaximumSize(QSize(32, 16777215))
        self.addWidget(self.forward_button)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(Translations["home.search_entries"])
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field_completion_list = QStringListModel()
        self.search_field_completer = QCompleter(
            self.search_field_completion_list, self.search_field
        )
        self.search_field_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_field.setCompleter(self.search_field_completer)
        self.addWidget(self.search_field)

        self.search_button = QPushButton(Translations["home.search"])
        self.search_button.setObjectName("search_button")
        self.search_button.setMinimumSize(QSize(0, 32))
        self.addWidget(self.search_button)
