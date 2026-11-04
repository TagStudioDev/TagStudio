# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math

from PIL import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QTextBrowser, QVBoxLayout

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.inset_frame import InsetFrame
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.stylesheets import header
from tagstudio.qt.views.styles.tagstudio_style import set_track_side_inset
from tagstudio.qt.views.styles.widget_effects import DEBOSSED_OUTLINE_WIDTH, widget_drop_shadow

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
        widget_drop_shadow(self.logo_label)

        self.title_label = QLabel(header(Translations["changelog.title"], 2))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_browser = QTextBrowser()
        # NOTE: Guard against stray internal markdown links breaking the page.
        # All links are opened by the controller class instead using the default browser.
        self.text_browser.setOpenLinks(False)
        self.text_browser.setStyleSheet("QTextBrowser { background: transparent; border: none; }")
        self.text_browser.document().setDocumentMargin(6)
        set_track_side_inset(self.text_browser.verticalScrollBar(), DEBOSSED_OUTLINE_WIDTH)
        text_box = InsetFrame()
        text_box_layout = QVBoxLayout(text_box)
        text_box_layout.setContentsMargins(
            DEBOSSED_OUTLINE_WIDTH, DEBOSSED_OUTLINE_WIDTH, 0, DEBOSSED_OUTLINE_WIDTH
        )
        text_box_layout.addWidget(self.text_browser)

        self.addSpacing(_TOP_SPACING)
        self.addWidget(self.logo_label)
        self.addWidget(self.title_label)
        self.addSpacing(6)
        self.addWidget(text_box)

        self.view_more_button = QPushButton(Translations["changelog.button.view_more"])
        self.view_more_button.setStyleSheet("QPushButton {padding: 3px 16px;}")
