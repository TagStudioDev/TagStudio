# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import Literal, override

from PIL import ImageQt
from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.landing_page_view import LandingPageView
from tagstudio.qt.views.styles.color_overlay import auto_theme_overlay


class LandingPage(QWidget):
    """A basic screen to show when no library is open.

    Shows the TagStudio logo and library Open/Create button.
    """

    open_library_requested = Signal()

    def __init__(self, pixel_ratio: float) -> None:
        super().__init__()
        self._rm = ResourceManager()

        self._logo_width = int(480 * pixel_ratio)
        self._pixel_ratio = pixel_ratio
        self._special_click_count = 0

        self.setLayout(LandingPageView())
        logo_label = self.layout().logo_label
        self._update_logo_color()

        # Logo Animation
        self._logo_pos_anim = QPropertyAnimation(logo_label, b"pos")
        self._logo_pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._logo_pos_anim.setDuration(1000)

        logo_opacity_effect = QGraphicsOpacityEffect(logo_label)
        logo_label.setGraphicsEffect(logo_opacity_effect)
        self._logo_opacity_anim = QPropertyAnimation(logo_opacity_effect, b"opacity")
        self._logo_opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._logo_opacity_anim.setDuration(1000)
        self._logo_opacity_anim.setStartValue(0.0)
        self._logo_opacity_anim.setEndValue(1.0)

        self._logo_special_anim = QPropertyAnimation(logo_label, b"pos")
        self._logo_special_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._logo_special_anim.setDuration(500)

        logo_label.clicked.connect(self._update_special_click)
        self.layout().open_button.clicked.connect(self.open_library_requested)

    @override
    def layout(self) -> LandingPageView:
        layout = super().layout()
        assert isinstance(layout, LandingPageView)
        return layout

    def set_status_label(self, text: str) -> None:
        """Set the text of the status label.

        Args:
            text (str): Text of the status to set.
        """
        self.layout().status_label.setText(text)

    def animate_logo_in(self) -> None:
        """Animate the TagStudio logo in."""
        logo_label = self.layout().logo_label
        self._logo_pos_anim.setStartValue(QPoint(logo_label.x(), logo_label.y() - 100))
        self._logo_pos_anim.setEndValue(logo_label.pos())
        self._logo_pos_anim.start()
        self._logo_opacity_anim.start()

    def _update_logo_color(self, style: Literal["mono", "color"] = "mono") -> None:
        """Update the color of the TagStudio logo.

        Args:
            style (str): The style of the logo. Either "mono" or "color".
        """
        if style == "mono":
            pixmap = auto_theme_overlay(self._rm.ts_logo_text_mono)
        else:
            pixmap = QPixmap.fromImage(ImageQt.ImageQt(self._rm.ts_logo_text_color))

        pixmap.setDevicePixelRatio(self._pixel_ratio)
        pixmap = pixmap.scaledToWidth(self._logo_width, Qt.TransformationMode.SmoothTransformation)
        logo_label = self.layout().logo_label
        logo_label.setMaximumSize(pixmap.deviceIndependentSize().toSize())
        logo_label.setPixmap(pixmap)

    def _update_special_click(self) -> None:
        """Increment the click count for the logo easter egg if it has not been triggered.

        If it reaches the click threshold, this triggers it and prevents it from triggering again.
        """
        if self._special_click_count >= 0:
            self._special_click_count += 1
            if self._special_click_count >= 10:
                self._update_logo_color("color")
                self._animate_logo_pop()
                self._special_click_count = -1

    def _animate_logo_pop(self) -> None:
        """Special pop animation for the TagStudio logo."""
        logo_label = self.layout().logo_label
        self._logo_special_anim.setStartValue(logo_label.pos())
        self._logo_special_anim.setKeyValueAt(0.25, QPoint(logo_label.x() - 5, logo_label.y()))
        self._logo_special_anim.setKeyValueAt(0.5, QPoint(logo_label.x() + 5, logo_label.y() - 10))
        self._logo_special_anim.setKeyValueAt(0.75, QPoint(logo_label.x() - 5, logo_label.y()))
        self._logo_special_anim.setEndValue(logo_label.pos())

        self._logo_special_anim.start()
