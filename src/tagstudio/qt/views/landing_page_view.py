# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import platform

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.clickable_label import ClickableLabel


class LandingPageView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSpacing(12)

        self.logo_label = ClickableLabel()

        open_shortcut_text = "(⌘ O)" if platform.system() == "Darwin" else "(Ctrl + O)"
        self.open_button = QPushButton(
            Translations.format("landing.open_create_library", shortcut=open_shortcut_text)
        )
        self.open_button.setMinimumWidth(200)

        self.status_label = QLabel()
        self.status_label.setMinimumWidth(200)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.addWidget(self.logo_label)
        self.addWidget(self.open_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
