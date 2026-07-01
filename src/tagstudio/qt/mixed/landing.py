# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import sys
import typing

import structlog
from PIL import Image, ImageQt
from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.qt.controllers.clickable_label import ClickableLabel
from tagstudio.qt.helpers.color_overlay import auto_theme_overlay
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class LandingWidget(QWidget):
    rm: ResourceManager = ResourceManager()
    mono_logo: Image.Image = rm.ts_logo_text_mono
    color_logo: Image.Image = rm.ts_logo_text_color

    def __init__(self, driver: "QtDriver", pixel_ratio: float):
        super().__init__()
        self.driver = driver
        self.logo_label: ClickableLabel = ClickableLabel()
        self._pixel_ratio: float = pixel_ratio
        self._logo_width: int = int(480 * pixel_ratio)
        self._special_click_count: int = 0

        # Create layout --------------------------------------------------------
        self.landing_layout = QVBoxLayout()
        self.landing_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.landing_layout.setSpacing(12)
        self.setLayout(self.landing_layout)

        # Create landing logo --------------------------------------------------
        self.landing_pixmap: QPixmap = QPixmap()
        self.update_logo_color()
        self.logo_label.clicked.connect(self._update_special_click)

        # Initialize landing logo animation ------------------------------------
        self.logo_pos_anim = QPropertyAnimation(self.logo_label, b"pos")
        self.logo_pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.logo_pos_anim.setDuration(1000)

        self.logo_special_anim = QPropertyAnimation(self.logo_label, b"pos")
        self.logo_special_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.logo_special_anim.setDuration(500)

        # Create "Open/Create Library" button ----------------------------------
        if sys.platform == "darwin":
            open_shortcut_text = "(⌘ + O)"
        else:
            open_shortcut_text = "(Ctrl + O)"
        self.open_button: QPushButton = QPushButton(
            Translations.format("landing.open_create_library", shortcut=open_shortcut_text)
        )
        self.open_button.setMinimumWidth(200)
        self.open_button.clicked.connect(self.driver.open_library_from_dialog)

        # Create status label --------------------------------------------------
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
        self.landing_layout.addWidget(self.open_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.landing_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def update_logo_color(self, style: typing.Literal["mono", "color"] = "mono"):
        """Update the color of the TagStudio logo.

        Args:
            style (str): = The style of the logo. Either "mono" or "color".
        """
        if style == "mono":
            logo_im = auto_theme_overlay(LandingWidget.mono_logo)
        elif style == "color":
            logo_im = LandingWidget.color_logo

        logo_final: Image.Image = Image.new(
            mode="RGBA", size=LandingWidget.mono_logo.size, color="#00000000"
        )

        logo_final.paste(logo_im, (0, 0), mask=LandingWidget.mono_logo)

        self.landing_pixmap = QPixmap.fromImage(ImageQt.ImageQt(logo_im))
        self.landing_pixmap.setDevicePixelRatio(self._pixel_ratio)
        self.landing_pixmap = self.landing_pixmap.scaledToWidth(
            self._logo_width, Qt.TransformationMode.SmoothTransformation
        )
        self.logo_label.setMaximumHeight(
            int(
                LandingWidget.mono_logo.size[1]
                * (LandingWidget.mono_logo.size[0] / self._logo_width)
            )
        )
        self.logo_label.setMaximumWidth(self._logo_width)
        self.logo_label.setPixmap(self.landing_pixmap)

    def _update_special_click(self):
        """Increment the click count for the logo easter egg if it has not been triggered.

        If it reaches the click threshold, this triggers it
        and prevents it from triggering again.
        """
        if self._special_click_count >= 0:
            self._special_click_count += 1
            if self._special_click_count >= 10:
                self.update_logo_color("color")
                self.animate_logo_pop()
                self._special_click_count = -1

    def animate_logo_in(self):
        """Animate the TagStudio logo in, if not opening a library on start."""
        if not self.driver.settings.open_last_loaded_on_startup and not self.driver.args.open:
            self.logo_pos_anim.setStartValue(QPoint(self.logo_label.x(), self.logo_label.y() - 100))
            self.logo_pos_anim.setEndValue(self.logo_label.pos())
            self.logo_pos_anim.start()

    def animate_logo_pop(self):
        """Special pop animation for the TagStudio logo."""
        self.logo_special_anim.setStartValue(self.logo_label.pos())
        self.logo_special_anim.setKeyValueAt(
            0.25, QPoint(self.logo_label.x() - 5, self.logo_label.y())
        )
        self.logo_special_anim.setKeyValueAt(
            0.5, QPoint(self.logo_label.x() + 5, self.logo_label.y() - 10)
        )
        self.logo_special_anim.setKeyValueAt(
            0.75, QPoint(self.logo_label.x() - 5, self.logo_label.y())
        )
        self.logo_special_anim.setEndValue(self.logo_label.pos())

        self.logo_special_anim.start()

    # def animate_status(self):
    #     # if self.status_label.y() > 50:
    #     logger.info(f"{self.status_label.pos()}")
    #     self.status_pos_anim.setStartValue(
    #         QPoint(self.status_label.x(), self.status_label.y() + 50)
    #     )
    #     self.status_pos_anim.setEndValue(self.status_label.pos())
    #     self.status_pos_anim.start()

    def set_status_label(self, text: str):
        """Set the text of the status label.

        Args:
            text (str): Text of the status to set.
        """
        # if text:
        #     self.animate_status()
        self.status_label.setText(text)
