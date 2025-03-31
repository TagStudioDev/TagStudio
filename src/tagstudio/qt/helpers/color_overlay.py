# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from tagstudio.qt.helpers.gradient import linear_gradient

# TODO: Consolidate the built-in QT theme values with the values
# here, in enums.py, and in palette.py.
_THEME_DARK_FG: str = "#FFFFFF77"
_THEME_LIGHT_FG: str = "#000000DD"
_THEME_DARK_BG: str = "#000000DD"
_THEME_LIGHT_BG: str = "#FFFFFF55"


def theme_fg_overlay(image: Image.Image, use_alpha: bool = True) -> Image.Image:
    """Overlay the foreground theme color onto an image.

    Args:
        image (Image): The PIL Image object to apply an overlay to.
        use_alpha (bool): Option to retain the base image's alpha value when applying the overlay.
    """
    dark_fg: str = _THEME_DARK_FG[:-2] if not use_alpha else _THEME_DARK_FG
    light_fg: str = _THEME_LIGHT_FG[:-2] if not use_alpha else _THEME_LIGHT_FG

    overlay_color = (
        dark_fg if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark else light_fg
    )

    im = Image.new(mode="RGBA", size=image.size, color=overlay_color)
    return _apply_overlay(image, im)


def gradient_overlay(image: Image.Image, gradient: list[str]) -> Image.Image:
    """Overlay a color gradient onto an image.

    Args:
        image (Image): The PIL Image object to apply an overlay to.
        gradient (list[str): A list of string hex color codes for use as
            the colors of the gradient.
    """
    im: Image.Image = _apply_overlay(image, linear_gradient(image.size, gradient))
    return im


def _apply_overlay(image: Image.Image, overlay: Image.Image) -> Image.Image:
    """Apply an overlay on top of an image using the image's alpha channel as a mask.

    Args:
        image (Image): The PIL Image object to apply an overlay to.
        overlay (Image): The PIL Image object to act as the overlay contents.
    """
    im: Image.Image = Image.new(mode="RGBA", size=image.size, color="#00000000")
    im.paste(overlay, (0, 0), mask=image)
    return im
