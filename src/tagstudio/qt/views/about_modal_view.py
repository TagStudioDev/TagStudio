# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math

from PIL import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFormLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from tagstudio.core.constants import (
    BUILD_TYPE,
    COPYRIGHT,
    DISCORD_URL,
    DOCS_URL,
    GITHUB_REPO_URL,
    VERSION,
)
from tagstudio.core.library.alchemy.constants import DB_VERSION
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.clickable_label import ClickableLabel
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.palette import MUTED_PURPLE
from tagstudio.qt.views.styles.stylesheets import form_content_style, header

_TOP_SPACING = 60
_LOGO_WIDTH = 384


class AboutModalView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(6, 0, 6, 0)
        self.setSpacing(12)

        # TagStudio Logo -------------------------------------------------------
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

        # Version --------------------------------------------------------------
        version_str = " ".join(
            [
                f"{Translations['about.version']}",
                f"{VERSION} {(' (' + Translations[BUILD_TYPE] + ')') if BUILD_TYPE else ''}",
            ]
        )
        self.version_label = QLabel(header(version_str, 2))
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Copyright ------------------------------------------------------------
        self.copyright_label = QLabel(COPYRIGHT)
        self.copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.copyright_label.setStyleSheet(f"QLabel {{color: {MUTED_PURPLE}}}")

        # Description ----------------------------------------------------------
        self.desc_label = QLabel(Translations["about.description"])
        self.desc_label.setMaximumWidth(500)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # System Info ----------------------------------------------------------
        self.system_info_widget = QWidget()
        self.system_info_layout = QFormLayout(self.system_info_widget)
        self.system_info_layout.setSpacing(4)
        self.system_info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # TagStudio Version
        self.version_content = QLabel()
        self.system_info_layout.addRow(QLabel(Translations["about.version"]), self.version_content)

        # Library DB Version
        db_version_content = QLabel(f"{DB_VERSION}")
        db_version_content.setStyleSheet(form_content_style())
        self.system_info_layout.addRow(
            QLabel(Translations["about.library_version"]), db_version_content
        )

        # Config Path
        self.config_path_content = ClickableLabel()
        self.config_path_content.setCursor(Qt.CursorShape.PointingHandCursor)
        self.config_path_content.setWordWrap(True)
        self.config_path_content.setStyleSheet(form_content_style())
        self.system_info_layout.addRow(
            QLabel(f"{Translations['about.config_path']}"), self.config_path_content
        )

        # TODO: Add row for "App Cache Path" (currently that TagStudio.ini file)

        # Optional Modules -----------------------------------------------------
        self.parent_optional_modules_widget = QWidget()
        self.parent_optional_modules_layout = QVBoxLayout(self.parent_optional_modules_widget)
        self.parent_optional_modules_layout.setContentsMargins(0, 0, 0, 0)
        self.parent_optional_modules_layout.setSpacing(0)

        # Subtitle
        self.optional_modules_label = QLabel(header(Translations["about.modules.title"], 4))

        self.optional_modules_widget = QWidget()
        self.optional_modules_layout = QFormLayout(self.optional_modules_widget)
        self.optional_modules_layout.setSpacing(4)
        self.optional_modules_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.ffmpeg_path_content = ClickableLabel()
        self.ffprobe_path_content = ClickableLabel()
        self.ripgrep_path_content = ClickableLabel()
        # NOTE: Don't localize these module names
        for title, content in (
            ("FFmpeg", self.ffmpeg_path_content),
            ("FFprobe", self.ffprobe_path_content),
            ("ripgrep", self.ripgrep_path_content),
        ):
            content.setStyleSheet(form_content_style())
            self.optional_modules_layout.addRow(QLabel(title), content)

        self.parent_optional_modules_layout.addWidget(self.optional_modules_label)
        self.parent_optional_modules_layout.addWidget(self.optional_modules_widget)

        # Links ----------------------------------------------------------------
        self.links_label = QLabel(
            f'<p><a href="{GITHUB_REPO_URL}">GitHub</a> | '
            f'<a href="{DOCS_URL}">{Translations["about.documentation"]}</a> | '
            f'<a href="{DISCORD_URL}">Discord</a></p>'
        )
        self.links_label.setStyleSheet(f"QLabel {{color: {MUTED_PURPLE}}}")
        self.links_label.setWordWrap(True)
        self.links_label.setOpenExternalLinks(True)
        self.links_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add Widgets to Layouts -----------------------------------------------
        self.addSpacing(_TOP_SPACING)
        self.addWidget(self.logo_label)
        self.addWidget(self.version_label)
        self.addWidget(self.desc_label)
        self.addWidget(self.system_info_widget)
        self.addWidget(self.parent_optional_modules_widget)
        self.addStretch(1)
        self.addWidget(self.links_label)
        self.addWidget(self.copyright_label)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
