# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

from PIL.Image import Image
from PIL.Image import new as new_image

from tagstudio.core.enums import Theme
from tagstudio.qt.views.styles.palette import ColorType, UiColor, get_ui_color


# TODO: Split out Qt color palette stuff from anything needed by the core.
def apply_overlay_color(image: Image, color: UiColor, theme: Theme) -> Image:
    """Apply a color overlay effect to an image based on its color channel data.

    Red channel for foreground, green channel for outline, none for background.

    Args:
        image (Image.Image): The image to apply an overlay to.
        color (UiColor): The name of the ColorType color to use.
        theme (Theme): A theme enum to determine the light/dark theme.
    """
    bg_color: str = (
        get_ui_color(ColorType.DARK_ACCENT, color)
        if theme == Theme.DARK
        else get_ui_color(ColorType.PRIMARY, color)
    )
    fg_color: str = (
        get_ui_color(ColorType.PRIMARY, color)
        if theme == Theme.DARK
        else get_ui_color(ColorType.LIGHT_ACCENT, color)
    )
    ol_color: str = (
        get_ui_color(ColorType.BORDER, color)
        if theme == Theme.DARK
        else get_ui_color(ColorType.LIGHT_ACCENT, color)
    )

    bg: Image = new_image(image.mode, image.size, color=bg_color)
    fg: Image = new_image(image.mode, image.size, color=fg_color)
    ol: Image = new_image(image.mode, image.size, color=ol_color)

    bg.paste(fg, (0, 0), mask=image.getchannel(0))
    bg.paste(ol, (0, 0), mask=image.getchannel(1))

    if image.mode == "RGBA":
        alpha_bg: Image = bg.copy()
        alpha_bg.convert("RGBA")
        alpha_bg.putalpha(0)
        alpha_bg.paste(bg, (0, 0), mask=image.getchannel(3))
        bg = alpha_bg

    return bg
