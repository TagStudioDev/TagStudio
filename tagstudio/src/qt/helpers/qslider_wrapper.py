# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtWidgets import QSlider, QStyle, QStyleOptionSlider


class QClickSlider(QSlider):
    """Custom QSlider wrapper.

    The purpose of this wrapper is to allow us to set slider positions
    based on click events.
    """

    mouse_pressed = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event):  # noqa: N802
        """Overide to handle mouse clicks.

        Overriding the mousePressEvent allows us to seek
        directly to the position the user clicked instead
        of stepping.
        """
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        handle_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self
        )

        was_slider_clicked = handle_rect.contains(event.position().x(), event.position().y())

        if was_slider_clicked:
            super().mousePressEvent(event)
        else:
            self.setValue(
                QStyle.sliderValueFromPosition(
                    self.minimum(), self.maximum(), event.x(), self.width()
                )
            )
            self.mouse_pressed = True

    def observe_mouse(self) -> bool:
        """Getter for the mouse_pressed property.

        This will also clear the mouse_pressed property
        if it is set. We do this so that consumers of slider
        events can modify the sliders position.
        """
        if self.mouse_pressed:
            self.mouse_pressed = False
            return True

        return False
