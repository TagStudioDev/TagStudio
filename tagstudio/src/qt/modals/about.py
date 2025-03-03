# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PIL import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from src.core.constants import VERSION, VERSION_BRANCH
from src.qt.modals.ffmpeg_checker import FfmpegChecker
from src.qt.resource_manager import ResourceManager
from src.qt.translations import Translations


class AboutModal(QWidget):
    def __init__(self, config_path):
        super().__init__()
        self.setWindowTitle(Translations["about.title"])

        self.fc: FfmpegChecker = FfmpegChecker()
        self.rm: ResourceManager = ResourceManager()

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(400, 500)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(20, 20, 20, 6)

        self.logo_widget = QLabel()
        self.logo_widget.setObjectName("logo")
        self.logo_pixmap = QPixmap.fromImage(ImageQt.ImageQt(self.rm.get("logo")))
        self.logo_pixmap = self.logo_pixmap.scaledToWidth(
            128, Qt.TransformationMode.SmoothTransformation
        )
        self.logo_widget.setPixmap(self.logo_pixmap)
        self.logo_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.logo_widget.setContentsMargins(0, 0, 0, 20)

        ff_version = self.fc.version()
        ffmpeg = '<span style="color:red">Missing</span>'
        if ff_version["ffmpeg"] is not None:
            ffmpeg = '<span style="color:green">Found</span> (' + ff_version["ffmpeg"] + ")"
        ffprobe = '<span style="color:red">Missing</span>'
        if ff_version["ffprobe"] is not None:
            ffprobe = '<span style="color:green">Found</span> (' + ff_version["ffprobe"] + ")"
        self.content_widget = QLabel(
            Translations["about.content"].format(
                version=VERSION,
                branch=VERSION_BRANCH,
                config_path=config_path,
                ffmpeg=ffmpeg,
                ffprobe=ffprobe,
            )
        )
        self.content_widget.setObjectName("contentLabel")
        self.content_widget.setWordWrap(True)
        self.content_widget.setOpenExternalLinks(True)
        self.content_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.button_widget = QWidget()
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.addStretch(1)

        self.close_button = QPushButton(Translations["generic.close"])
        self.close_button.clicked.connect(lambda: self.close())
        self.close_button.setMaximumWidth(80)

        self.button_layout.addWidget(self.close_button)

        self.root_layout.addWidget(self.logo_widget)
        self.root_layout.addWidget(self.content_widget, Qt.AlignmentFlag.AlignTop)
        self.root_layout.addWidget(self.button_widget)
