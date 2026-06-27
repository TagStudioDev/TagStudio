# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from pathlib import Path

from PIL import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.constants import (
    DISCORD_URL,
    DOCS_URL,
    GITHUB_REPO_URL,
    VERSION,
    VERSION_BRANCH,
)
from tagstudio.core.ts_core import TagStudioCore
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.models.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.previews.vendored import ffmpeg
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.stylesheets.stylesheets import form_content_style, header


class AboutModal(QWidget):
    def __init__(self, config_path: Path | str):
        super().__init__()
        self.setWindowTitle(Translations["about.title"])

        self.rm: ResourceManager = ResourceManager()

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(360, 540)
        self.setMaximumSize(600, 600)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 12, 0, 0)
        self.root_layout.setSpacing(0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(12)

        # TagStudio Icon Logo --------------------------------------------------
        self.logo_widget = QLabel()
        self.logo_pixmap = QPixmap.fromImage(ImageQt.ImageQt(self.rm.get("icon")))
        self.logo_pixmap.setDevicePixelRatio(self.devicePixelRatio())
        self.logo_pixmap = self.logo_pixmap.scaledToWidth(
            math.floor(128 * self.devicePixelRatio()), Qt.TransformationMode.SmoothTransformation
        )
        self.logo_widget.setPixmap(self.logo_pixmap)
        self.logo_widget.setContentsMargins(0, 0, 0, 0)
        self.logo_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title ----------------------------------------------------------------
        branch: str = (" (" + VERSION_BRANCH + ")") if VERSION_BRANCH else ""
        # NOTE: Do not localize program name.
        self.title_label = QLabel(header(f"TagStudio Alpha {VERSION}{branch}", 2))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Description ----------------------------------------------------------
        self.desc_label = QLabel(Translations["about.description"])
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # System Info ----------------------------------------------------------
        ff_version = ffmpeg.version()
        red = get_ui_color(ColorType.PRIMARY, UiColor.RED)
        green = get_ui_color(ColorType.PRIMARY, UiColor.GREEN)
        missing = Translations["generic.missing"]
        found = Translations["about.module.found"]

        ffmpeg_status = f'<span style="color:{red}">{missing}</span>'
        if ff_version["ffmpeg"] is not None:
            ffmpeg_status = (
                f'<span style="color:{green}">{found}</span> (' + ff_version["ffmpeg"] + ")"
            )

        ffprobe_status = f'<span style="color:{red}">{missing}</span>'
        if ff_version["ffprobe"] is not None:
            ffprobe_status = (
                f'<span style="color:{green}">{found}</span> (' + ff_version["ffprobe"] + ")"
            )

        self.system_info_widget = QWidget()
        self.system_info_layout = QFormLayout(self.system_info_widget)
        self.system_info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Version
        version_title = QLabel(Translations["about.version"])
        latest_version = unwrap(TagStudioCore.get_most_recent_release_version(), "?")
        version_content_style = form_content_style()
        if latest_version == VERSION:
            version_content = QLabel(f"{VERSION}")
        else:
            version_content = QLabel(
                Translations.format(
                    "about.version.latest", built_version=VERSION, latest_version=latest_version
                )
            )
            version_content_style += f"color: {red};"
        version_content.setStyleSheet(version_content_style)
        version_content.setMaximumWidth(version_content.sizeHint().width())
        self.system_info_layout.addRow(version_title, version_content)

        # License
        license_title = QLabel(f"{Translations['about.license']}")
        license_content = QLabel("GPLv3")
        license_content.setStyleSheet(form_content_style())
        license_content.setMaximumWidth(license_content.sizeHint().width())
        self.system_info_layout.addRow(license_title, license_content)

        # Config Path
        config_path_title = QLabel(f"{Translations['about.config_path']}")
        config_path_content = QLabel(f"{config_path}")
        config_path_content.setStyleSheet(form_content_style())
        config_path_content.setWordWrap(True)
        self.system_info_layout.addRow(config_path_title, config_path_content)

        # FFmpeg Status
        ffmpeg_path_title = QLabel("FFmpeg")
        ffmpeg_path_content = QLabel(f"{ffmpeg_status}")
        ffmpeg_path_content.setStyleSheet(form_content_style())
        ffmpeg_path_content.setMaximumWidth(ffmpeg_path_content.sizeHint().width())
        self.system_info_layout.addRow(ffmpeg_path_title, ffmpeg_path_content)

        # FFprobe Status
        ffprobe_path_title = QLabel("FFprobe")
        ffprobe_path_content = QLabel(f"{ffprobe_status}")
        ffprobe_path_content.setStyleSheet(form_content_style())
        ffprobe_path_content.setMaximumWidth(ffprobe_path_content.sizeHint().width())
        self.system_info_layout.addRow(ffprobe_path_title, ffprobe_path_content)

        # Links ----------------------------------------------------------------

        self.links_label = QLabel(
            f'<p><a href="{GITHUB_REPO_URL}">GitHub</a> | '
            f'<a href="{DOCS_URL}">{Translations["about.documentation"]}</a> | '
            f'<a href="{DISCORD_URL}">Discord</a></p>'
        )
        self.links_label.setWordWrap(True)
        self.links_label.setOpenExternalLinks(True)
        self.links_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Buttons --------------------------------------------------------------
        self.button_widget = QWidget()
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.setContentsMargins(12, 12, 12, 12)
        self.button_layout.addStretch(1)

        self.close_button = QPushButton(Translations["generic.close"])
        self.close_button.clicked.connect(lambda: self.close())
        self.button_layout.addWidget(self.close_button)

        # Add Widgets to Layouts -----------------------------------------------
        self.content_layout.addWidget(self.logo_widget)
        self.content_layout.addWidget(self.title_label)
        self.content_layout.addWidget(self.desc_label)
        self.content_layout.addWidget(self.system_info_widget)
        self.content_layout.addWidget(self.links_label)
        self.content_layout.addStretch(1)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.root_layout.addWidget(self.content_widget)
        self.root_layout.addWidget(self.button_widget)
