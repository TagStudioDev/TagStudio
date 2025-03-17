# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from typing import override

from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QSlider, QStyle, QStyleOptionSlider


class QClickSlider(QSlider):
    """Custom QSlider wrapper.

    The purpose of this wrapper is to allow us to set slider positions
    based on click events.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @override
    def mousePressEvent(self, ev: QMouseEvent):
        """Override to handle mouse clicks.

        Overriding the mousePressEvent allows us to seek
        directly to the position the user clicked instead
        of stepping.
        """
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        handle_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self
        )

        was_slider_clicked = handle_rect.contains(int(ev.position().x()), int(ev.position().y()))

        if not was_slider_clicked:
            self.setValue(
                QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), ev.x(), self.width())
            )
            self.mouse_pressed = True

        super().mousePressEvent(ev)
