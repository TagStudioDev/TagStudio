# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import sys
import typing
from pathlib import Path
from PIL import Image, ImageQt
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
# from src.qt.helpers.gradient import linear_gradient

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logging.basicConfig(format="%(message)s", level=logging.INFO)


class LandingWidget(QWidget):
    def __init__(self, driver: "QtDriver", pixel_ratio: float):
        super().__init__()
        self.driver: "QtDriver" = driver
        self.logo_label: QLabel = QLabel()
        self.pixel_ratio: float = pixel_ratio
        self.logo_width: int = int(480 * pixel_ratio)

        # Create layout --------------------------------------------------------
        self.landing_layout = QVBoxLayout()
        self.landing_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.landing_layout.setSpacing(12)
        self.setLayout(self.landing_layout)

        # Create landing logo --------------------------------------------------
        # self.landing_logo_pixmap = QPixmap(":/images/tagstudio_logo_text_mono.png")
        logo_raw: Image.Image = Image.open(
            Path(__file__).parents[3]
            / "resources/qt/images/tagstudio_logo_text_mono.png"
        )
        # TODO: Make this a generic process that other assets can use.
        # TODO: Allow this to be updated when the theme changes at runtime.
        overlay_dark: str = "#FFFFFF55"
        overlay_light: str = "#000000DD"
        logging.info(QGuiApplication.styleHints().colorScheme())
        overlay_color = (
            overlay_dark
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else overlay_light
        )

        logo_overlay: Image.Image = Image.new(
            mode="RGBA", size=logo_raw.size, color=overlay_color
        )

        # NOTE: This produces a gradient overlay effect similar to the normal
        # colored TagStudio logo. Currently unused but available for the future.
        # rainbow_colors: list[str] = ["#d27bf4", "#7992f5", "#63c6e3", "#63f5cf"]
        # logo_overlay: Image.Image = linear_gradient(logo_raw.size, rainbow_colors)

        logo_final: Image.Image = Image.new(
            mode="RGBA", size=logo_raw.size, color="#00000000"
        )
        logo_final.paste(logo_overlay, (0, 0), mask=logo_raw)

        self.landing_pixmap: QPixmap = QPixmap.fromImage(ImageQt.ImageQt(logo_final))
        self.landing_pixmap.setDevicePixelRatio(self.pixel_ratio)
        self.landing_pixmap = self.landing_pixmap.scaledToWidth(
            self.logo_width, Qt.TransformationMode.SmoothTransformation
        )
        self.logo_label.setPixmap(self.landing_pixmap)
        self.logo_label.setMaximumHeight(
            int(logo_final.size[1] * (logo_final.size[0] / self.logo_width))
        )
        self.logo_label.setMaximumWidth(self.logo_width)

        # Initialize landing logo animation ------------------------------------
        self.logo_pos_anim = QPropertyAnimation(self.logo_label, b"pos")
        self.logo_pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.logo_pos_anim.setDuration(1000)

        # Create "Open/Create Library" button
        open_shortcut_text: str = ""
        if sys.platform == "Darwin":
            open_shortcut_text = "(⌘Command + O)"
        else:
            open_shortcut_text = "(Ctrl + O)"
        self.open_button: QPushButton = QPushButton()
        self.open_button.setMinimumWidth(200)
        self.open_button.setText(f"Open/Create Library {open_shortcut_text}")
        self.open_button.clicked.connect(self.driver.open_library_from_dialog)

        self.status_label = QLabel()
        self.status_label.setMinimumWidth(200)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setText("")

        # Initialize landing logo animation ------------------------------------
        self.status_pos_anim = QPropertyAnimation(self.status_label, b"pos")
        self.status_pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.status_pos_anim.setDuration(500)

        # Add widgets to layout ------------------------------------------------
        self.landing_layout.addWidget(self.logo_label)
        self.landing_layout.addWidget(
            self.open_button, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.landing_layout.addWidget(
            self.status_label, alignment=Qt.AlignmentFlag.AlignCenter
        )

    def animate_logo(self):
        # NOTE: Sometimes, mostly on startup without a library open, the
        # y position of logo_label is something like 10. I'm not sure what
        # the cause of this is, so I've just done this workaround to disable
        # the animation if the y position is too incorrect.
        if self.logo_label.y() > 50:
            logging.info(f"{self.logo_label.pos()}")
            self.logo_pos_anim.setStartValue(
                QPoint(self.logo_label.x(), self.logo_label.y() - 100)
            )
            self.logo_pos_anim.setEndValue(self.logo_label.pos())
            self.logo_pos_anim.start()

    # def animate_status(self):
    #     # if self.status_label.y() > 50:
    #     logging.info(f"{self.status_label.pos()}")
    #     self.status_pos_anim.setStartValue(
    #         QPoint(self.status_label.x(), self.status_label.y() + 50)
    #     )
    #     self.status_pos_anim.setEndValue(self.status_label.pos())
    #     self.status_pos_anim.start()

    def set_status_label(self, text=str):
        # if text:
        #     self.animate_status()
        self.status_label.setText(text)
