# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math

from PIL import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.constants import VERSION, VERSION_BRANCH
from tagstudio.core.enums import Theme
from tagstudio.core.ts_core import TagStudioCore
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.models.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.previews.vendored import ffmpeg
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations


class AboutModal(QWidget):
    def __init__(self, config_path):
        super().__init__()
        self.setWindowTitle(Translations["about.title"])

        self.rm: ResourceManager = ResourceManager()

        # TODO: There should be a global button theme somewhere.
        self.form_content_style = (
            f"background-color:{
                Theme.COLOR_BG.value
                if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
                else Theme.COLOR_BG_LIGHT.value
            };"
            "border-radius:3px;"
            "font-weight: 500;"
            "padding: 2px;"
        )

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
        self.title_label = QLabel(f"<h2>TagStudio Alpha {VERSION}{branch}</h2>")
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
        version_title = QLabel("Version")
        most_recent_release = unwrap(TagStudioCore.get_most_recent_release_version(), "UNKNOWN")
        version_content_style = self.form_content_style
        if most_recent_release == VERSION:
            version_content = QLabel(f"{VERSION}")
        else:
            version_content = QLabel(f"{VERSION} (Latest Release: {most_recent_release})")
            version_content_style += "color: #d9534f;"
        version_content.setStyleSheet(version_content_style)
        version_content.setMaximumWidth(version_content.sizeHint().width())
        self.system_info_layout.addRow(version_title, version_content)

        # License
        license_title = QLabel(f"{Translations['about.license']}")
        license_content = QLabel("GPLv3")
        license_content.setStyleSheet(self.form_content_style)
        license_content.setMaximumWidth(license_content.sizeHint().width())
        self.system_info_layout.addRow(license_title, license_content)

        # Config Path
        config_path_title = QLabel(f"{Translations['about.config_path']}")
        config_path_content = QLabel(f"{config_path}")
        config_path_content.setStyleSheet(self.form_content_style)
        config_path_content.setWordWrap(True)
        self.system_info_layout.addRow(config_path_title, config_path_content)

        # FFmpeg Status
        ffmpeg_path_title = QLabel("FFmpeg")
        ffmpeg_path_content = QLabel(f"{ffmpeg_status}")
        ffmpeg_path_content.setStyleSheet(self.form_content_style)
        ffmpeg_path_content.setMaximumWidth(ffmpeg_path_content.sizeHint().width())
        self.system_info_layout.addRow(ffmpeg_path_title, ffmpeg_path_content)

        # FFprobe Status
        ffprobe_path_title = QLabel("FFprobe")
        ffprobe_path_content = QLabel(f"{ffprobe_status}")
        ffprobe_path_content.setStyleSheet(self.form_content_style)
        ffprobe_path_content.setMaximumWidth(ffprobe_path_content.sizeHint().width())
        self.system_info_layout.addRow(ffprobe_path_title, ffprobe_path_content)

        # Links ----------------------------------------------------------------
        repo_link = "https://github.com/TagStudioDev/TagStudio"
        docs_link = "https://docs.tagstud.io"
        discord_link = "https://discord.com/invite/hRNnVKhF2G"

        self.links_label = QLabel(
            f'<p><a href="{repo_link}">GitHub</a> | '
            f'<a href="{docs_link}">{Translations["about.documentation"]}</a> | '
            f'<a href="{discord_link}">Discord</a></p>'
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
