# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PIL import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.constants import VERSION, VERSION_BRANCH
from src.qt.resource_manager import ResourceManager
from src.qt.translations import Translations


class AboutModal(QWidget):
    def __init__(self):
        super().__init__()
        Translations.translate_with_setter(self.setWindowTitle, "about.title")

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

        self.content_widget = QLabel()
        self.content_widget.setObjectName("contentLabel")
        self.content_widget.setWordWrap(True)
        Translations.translate_qobject(
            self.content_widget,
            "about.content",
            version=VERSION,
            branch=VERSION_BRANCH,
        )
        self.content_widget.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.button_widget = QWidget()
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.addStretch(1)

        self.close_button = QPushButton()
        Translations.translate_qobject(self.close_button, "generic.close")
        self.close_button.clicked.connect(lambda: self.close())
        self.close_button.setMaximumWidth(80)

        self.button_layout.addWidget(self.close_button)

        self.root_layout.addWidget(self.logo_widget)
        self.root_layout.addWidget(self.content_widget, Qt.AlignmentFlag.AlignTop)
        self.root_layout.addWidget(self.button_widget)
