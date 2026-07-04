# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from pathlib import Path

from PIL import ImageQt
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QPixmap
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
    COPYRIGHT,
    DISCORD_URL,
    DOCS_URL,
    GITHUB_REPO_URL,
    VERSION,
    VERSION_BRANCH,
)
from tagstudio.core.ts_core import TagStudioCore
from tagstudio.core.utils.ffmpeg_status import FfmpegStatus, FfprobeStatus
from tagstudio.core.utils.ripgrep_status import RipgrepStatus
from tagstudio.core.utils.str_formatting import is_version_outdated
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.clickable_label import ClickableLabel
from tagstudio.qt.models.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations
from tagstudio.qt.utils.file_opener import open_file
from tagstudio.qt.views.stylesheets.stylesheets import form_content_style


class AboutModal(QWidget):
    """Modal window showing information about the TagStudio application."""

    VERSION_STR: str = f"{Translations['about.version']} {VERSION} {(' (' + VERSION_BRANCH + ')') if VERSION_BRANCH else ''}"  # noqa: E501

    def __init__(self, config_path: Path | str):
        super().__init__()
        self.setWindowTitle(Translations["about.title"])

        self.rm: ResourceManager = ResourceManager()
        pixel_ratio = self.devicePixelRatio()
        self.setStyleSheet("QLabel {color: white}")

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedWidth(600)
        self.setMinimumHeight(600)
        self.setMaximumHeight(900)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 100, 0, 0)
        self.root_layout.setSpacing(0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(12)

        # TagStudio Logo -------------------------------------------------------
        self.logo_widget = QLabel()
        self.logo_pixmap = QPixmap.fromImage(ImageQt.ImageQt(self.rm.ts_logo_text_color))
        self.logo_pixmap.setDevicePixelRatio(pixel_ratio)
        self.logo_pixmap = self.logo_pixmap.scaledToWidth(
            math.floor(384 * self.devicePixelRatio()), Qt.TransformationMode.SmoothTransformation
        )
        self.logo_widget.setPixmap(self.logo_pixmap)
        self.logo_widget.setContentsMargins(0, 0, 0, 0)
        self.logo_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Version --------------------------------------------------------------
        self.version_label = QLabel(f"<h3>{AboutModal.VERSION_STR}</h3>")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Copyright ------------------------------------------------------------
        self.copyright_label = QLabel(COPYRIGHT)
        self.copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.copyright_label.setStyleSheet("QLabel {color: #809782ff}")

        # Description ----------------------------------------------------------
        self.desc_label = QLabel(Translations["about.description"])
        self.desc_label.setMaximumWidth(500)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # System Info ----------------------------------------------------------
        ffmpeg_ver = FfmpegStatus.version()
        ffprobe_ver = FfprobeStatus.version()
        ripgrep_ver = RipgrepStatus.version()
        red = get_ui_color(ColorType.PRIMARY, UiColor.RED)
        green = get_ui_color(ColorType.PRIMARY, UiColor.GREEN)
        amber = get_ui_color(ColorType.PRIMARY, UiColor.AMBER)
        missing = Translations["generic.missing"]
        found = Translations["about.module.found"]

        ffmpeg_status = f'<span style="color:{red}">{missing}</span>'
        if ffmpeg_ver is not None:
            ffmpeg_status = f'<span style="color:{green}">{found}</span> (' + ffmpeg_ver + ")"

        ffprobe_status = f'<span style="color:{red}">{missing}</span>'
        if ffprobe_ver is not None:
            ffprobe_status = f'<span style="color:{green}">{found}</span> (' + ffprobe_ver + ")"

        ripgrep_status = f'<span style="color:{amber}">{missing}</span>'
        if ripgrep_ver is not None:
            ripgrep_status = f'<span style="color:{green}">{found}</span> (' + ripgrep_ver + ")"

        self.system_info_widget = QWidget()
        self.system_info_layout = QFormLayout(self.system_info_widget)
        self.system_info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Version
        version_title = QLabel(Translations["about.version"])
        latest_version = unwrap(TagStudioCore.get_most_recent_release_version(), "0.0.0")
        version_content_style = form_content_style()
        if not is_version_outdated(VERSION, latest_version):
            version_content = QLabel(f"{VERSION}")
        else:
            version_content = QLabel(
                Translations.format(
                    "about.version.latest", built_version=VERSION, latest_version=latest_version
                )
            )
            version_content_style += f"color: {red};"
        version_content.setStyleSheet(version_content_style)
        self.system_info_layout.addRow(version_title, version_content)
        version_content.setMaximumWidth(version_content.sizeHint().width())

        # Config Path
        config_path_title = QLabel(f"{Translations['about.config_path']}")
        config_path_content = ClickableLabel(f"{config_path}")
        config_path_content.clicked.connect(lambda: open_file(config_path, file_manager=True))
        config_path_content.setCursor(Qt.CursorShape.PointingHandCursor)
        config_path_content.setWordWrap(True)
        config_path_content.setStyleSheet(form_content_style())
        self.system_info_layout.addRow(config_path_title, config_path_content)

        # TODO: Add row for "App Cache Path" (currently that TagStudio.ini file)

        # FFmpeg Status
        ffmpeg_path_title = QLabel("FFmpeg")
        ffmpeg_path_content = ClickableLabel(f"{ffmpeg_status}")
        ffmpeg_location = FfmpegStatus.which()
        if ffmpeg_location:
            ffmpeg_path_content.clicked.connect(
                lambda: open_file(ffmpeg_location, file_manager=True)
            )
            ffmpeg_path_content.setCursor(Qt.CursorShape.PointingHandCursor)
        ffmpeg_path_content.setStyleSheet(form_content_style())
        self.system_info_layout.addRow(ffmpeg_path_title, ffmpeg_path_content)
        ffmpeg_path_content.setMaximumWidth(ffmpeg_path_content.sizeHint().width())

        # FFprobe Status
        ffprobe_path_title = QLabel("FFprobe")
        ffprobe_path_content = ClickableLabel(f"{ffprobe_status}")
        ffprobe_location = FfprobeStatus.which()
        if ffprobe_location:
            ffprobe_path_content.clicked.connect(
                lambda: open_file(ffprobe_location, file_manager=True)
            )
            ffprobe_path_content.setCursor(Qt.CursorShape.PointingHandCursor)
        ffprobe_path_content.setStyleSheet(form_content_style())
        self.system_info_layout.addRow(ffprobe_path_title, ffprobe_path_content)
        ffprobe_path_content.setMaximumWidth(ffprobe_path_content.sizeHint().width())

        # ripgrep Status
        # TODO: Add a central class to find ripgrep info, similar to ffmpeg
        ripgrep_path_title = QLabel("ripgrep")  # NOTE: Don't localize
        ripgrep_path_content = ClickableLabel()
        ripgrep_path_content.setText(f"{ripgrep_status}")  # TODO: Pass in constructor after #1386
        ripgrep_location = RipgrepStatus.which()
        if ripgrep_location:
            ripgrep_path_content.clicked.connect(
                lambda: open_file(ripgrep_location, file_manager=True)
            )
            ripgrep_path_content.setCursor(Qt.CursorShape.PointingHandCursor)
        ripgrep_path_content.setStyleSheet(form_content_style())
        ripgrep_path_content.setMaximumWidth(ripgrep_path_content.sizeHint().width())
        self.system_info_layout.addRow(ripgrep_path_title, ripgrep_path_content)

        # Links ----------------------------------------------------------------

        self.links_label = QLabel(
            f'<p><a href="{GITHUB_REPO_URL}">GitHub</a> | '
            f'<a href="{DOCS_URL}">{Translations["about.documentation"]}</a> | '
            f'<a href="{DISCORD_URL}">Discord</a></p>'
        )
        self.links_label.setStyleSheet("QLabel {color: #809782ff}")
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
        self.content_layout.addWidget(self.version_label)
        self.content_layout.addWidget(self.desc_label)
        self.content_layout.addWidget(self.system_info_widget)
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(self.links_label)
        self.content_layout.addWidget(self.copyright_label)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.bg_image = self.rm.about_bg
        self.bg_image.setDevicePixelRatio(pixel_ratio)
        self.bg_image = self.bg_image.scaled(
            QSize(
                math.floor(self.width() * pixel_ratio),
                math.floor(self.maximumHeight() * pixel_ratio),
            ),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        palette = QPalette()
        palette.setBrush(QPalette.ColorRole.Window, self.bg_image)
        self.setPalette(palette)

        self.root_layout.addWidget(self.content_widget)
        self.root_layout.addWidget(self.button_widget)
