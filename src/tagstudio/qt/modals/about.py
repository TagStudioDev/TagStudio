# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PIL import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.constants import VERSION, VERSION_BRANCH
from tagstudio.core.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.modals.ffmpeg_checker import FfmpegChecker
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations


class AboutModal(QWidget):
    def __init__(self, config_path):
        super().__init__()
        self.setWindowTitle(Translations["about.title"])

        self.fc: FfmpegChecker = FfmpegChecker()
        self.rm: ResourceManager = ResourceManager()

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(360, 480)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(24, 24, 24, 6)
        self.root_layout.setSpacing(12)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.logo_widget = QLabel()
        self.logo_widget.setObjectName("logo")
        self.logo_pixmap = QPixmap.fromImage(ImageQt.ImageQt(self.rm.get("icon")))
        self.logo_pixmap = self.logo_pixmap.scaledToWidth(
            128, Qt.TransformationMode.SmoothTransformation
        )
        self.logo_widget.setPixmap(self.logo_pixmap)
        self.logo_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.logo_widget.setContentsMargins(0, 0, 0, 24)

        ff_version = self.fc.version()
        red = get_ui_color(ColorType.PRIMARY, UiColor.RED)
        green = get_ui_color(ColorType.PRIMARY, UiColor.GREEN)

        ffmpeg = f'<span style="color:{red}">Missing</span>'
        if ff_version["ffmpeg"] is not None:
            ffmpeg = f'<span style="color:{green}">Found</span> (' + ff_version["ffmpeg"] + ")"

        ffprobe = f'<span style="color:{red}">Missing</span>'
        if ff_version["ffprobe"] is not None:
            ffprobe = f'<span style="color:{green}">Found</span> (' + ff_version["ffprobe"] + ")"

        branch: str = (" (" + VERSION_BRANCH + ")") if VERSION_BRANCH else ""
        self.title_label = QLabel(f"<h2>TagStudio Alpha {VERSION}{branch}</h2>")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.content_label = QLabel(
            Translations.format(
                "about.content", config_path=config_path, ffmpeg=ffmpeg, ffprobe=ffprobe
            )
        )
        self.content_label.setObjectName("contentLabel")
        self.content_label.setWordWrap(True)
        self.content_label.setOpenExternalLinks(True)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.button_widget = QWidget()
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.addStretch(1)

        self.close_button = QPushButton(Translations["generic.close"])
        self.close_button.clicked.connect(lambda: self.close())

        self.button_layout.addWidget(self.close_button)

        self.root_layout.addWidget(self.logo_widget)
        self.root_layout.addWidget(self.title_label)
        self.root_layout.addWidget(self.content_label)
        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.button_widget)
