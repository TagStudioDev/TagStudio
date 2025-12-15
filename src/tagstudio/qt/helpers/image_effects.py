# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from tagstudio.qt.models.palette import ColorType, UiColor, get_ui_color


def replace_transparent_pixels(
    img: Image.Image, color: tuple[int, int, int, int] = (255, 255, 255, 255)
) -> Image.Image:
    """Replace (copying/without mutating) all transparent pixels in an image with the color.

    Args:
        img (Image.Image):
            The source image
        color (tuple[int, int, int, int]):
            The color (RGBA, 0 to 255) which transparent pixels should be set to.
            Defaults to white (255, 255, 255, 255)

    Returns:
        Image.Image:
            A copy of img with the pixels replaced.
    """
    pixel_array = np.asarray(img.convert("RGBA")).copy()
    pixel_array[pixel_array[:, :, 3] == 0] = color
    return Image.fromarray(pixel_array)


def apply_overlay_color(image: Image.Image, color: UiColor) -> Image.Image:
    """Apply a color overlay effect to an image based on its color channel data.

    Red channel for foreground, green channel for outline, none for background.

    Args:
        image (Image.Image): The image to apply an overlay to.
        color (UiColor): The name of the ColorType color to use.
    """
    bg_color: str = (
        get_ui_color(ColorType.DARK_ACCENT, color)
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else get_ui_color(ColorType.PRIMARY, color)
    )
    fg_color: str = (
        get_ui_color(ColorType.PRIMARY, color)
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else get_ui_color(ColorType.LIGHT_ACCENT, color)
    )
    overlay_color: str = (
        get_ui_color(ColorType.BORDER, color)
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else get_ui_color(ColorType.LIGHT_ACCENT, color)
    )

    bg: Image.Image = Image.new(image.mode, image.size, color=bg_color)
    fg: Image.Image = Image.new(image.mode, image.size, color=fg_color)
    overlay: Image.Image = Image.new(image.mode, image.size, color=overlay_color)

    bg.paste(fg, (0, 0), mask=image.getchannel(0))
    bg.paste(overlay, (0, 0), mask=image.getchannel(1))

    if image.mode == "RGBA":
        alpha_bg: Image.Image = bg.copy()
        alpha_bg.convert("RGBA")
        alpha_bg.putalpha(0)
        alpha_bg.paste(bg, (0, 0), mask=image.getchannel(3))
        bg = alpha_bg

    return bg
