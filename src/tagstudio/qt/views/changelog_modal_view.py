# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math

from PIL import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QTextBrowser, QVBoxLayout

from tagstudio.core.enums import ThemePalette
from tagstudio.i18n.translations import Translations
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.stylesheets import header

_TOP_SPACING = 60
_LOGO_WIDTH = 384


class ChangelogModalView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(6, 0, 6, 0)

        self.logo_label = QLabel()
        logo = QPixmap.fromImage(ImageQt.ImageQt(ResourceManager().ts_logo_text_color))
        pixel_ratio = self.logo_label.devicePixelRatio()
        logo.setDevicePixelRatio(pixel_ratio)
        self.logo_label.setPixmap(
            logo.scaledToWidth(
                math.floor(_LOGO_WIDTH * pixel_ratio), Qt.TransformationMode.SmoothTransformation
            )
        )
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(header(Translations["changelog.title"], 2))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_browser = QTextBrowser()
        # NOTE: Guard against stray internal markdown links breaking the page.
        # All links are opened by the controller class instead using the default browser.
        self.text_browser.setOpenLinks(False)
        self.text_browser.setStyleSheet(
            "QTextBrowser {"
            f"background: {ThemePalette.COLOR_BG_DARK.value};"
            "border: none;"
            "border-radius: 6px;"
            "color: white;"
            "}"
        )
        self.text_browser.document().setDocumentMargin(6)

        self.addSpacing(_TOP_SPACING)
        self.addWidget(self.logo_label)
        self.addWidget(self.title_label)
        self.addSpacing(6)
        self.addWidget(self.text_browser)

        self.view_more_button = QPushButton(Translations["changelog.button.view_more"])
        self.view_more_button.setStyleSheet("QPushButton {padding: 3px 16px;}")
