# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from pathlib import Path
from typing import cast, override

import numpy as np
import structlog
from PIL import ImageDraw, ImageFont
from PIL.Image import Image, Resampling, fromarray
from PIL.Image import new as new_image

from tagstudio.core.constants import FONT_SAMPLE_SIZES, FONT_SAMPLE_TEXT
from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.effects import apply_overlay_color
from tagstudio.qt.helpers.text_wrapper import wrap_full_text
from tagstudio.qt.views.styles.color_overlay import auto_theme_overlay
from tagstudio.qt.views.styles.palette import UiColor

logger = structlog.get_logger(__name__)


MediaTypes.register("font", ".otf", RENDER)
MediaTypes.register("font", ".ttc", RENDER)
MediaTypes.register("font", ".ttf", RENDER)


class FontPreview(BasePreview):
    media_type_name = "font"

    @override
    @classmethod
    def render(
        cls,
        filepath: Path,
        is_small: bool,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image | None:
        return (
            font_small_thumb(filepath, theme, size)
            if is_small
            else font_full_preview(filepath, size)
        )


def font_small_thumb(filepath: Path, theme: Theme, size: tuple[int, int]) -> Image | None:
    """Render a small font preview ("Aa") thumbnail from a font file.

    Args:
        filepath (Path): The path of the file.
        theme (Theme): The system color theme.
        size (tuple[int,int]): The size of the thumbnail.
    """
    # TODO: Support for non-square images
    im: Image | None = None
    try:
        bg = new_image("RGB", size, color="#000000")
        raw = new_image("RGB", (size[0] * 3, size[1] * 3), color="#000000")
        draw = ImageDraw.Draw(raw)
        font = ImageFont.truetype(filepath, size=size[0])
        # NOTE: While a stroke effect is desired, the text
        # method only allows for outer strokes, which looks
        # a bit weird when rendering fonts.
        draw.text(
            (size[0] // 8, size[1] // 8),
            "Aa",
            font=font,
            fill="#FF0000",
            # stroke_width=math.ceil(size / 96),
            # stroke_fill="#FFFF00",
        )
        # NOTE: Change to getchannel(1) if using an outline.
        data = np.asarray(raw.getchannel(0))

        m, n = data.shape[:2]
        col: np.ndarray = cast(np.ndarray, data.any(0))
        row: np.ndarray = cast(np.ndarray, data.any(1))
        cropped_data = np.asarray(raw)[
            row.argmax() : m - row[::-1].argmax(),
            col.argmax() : n - col[::-1].argmax(),
        ]
        cropped_im: Image = fromarray(cropped_data, "RGB")

        margin: int = math.ceil(size[0] // 16)

        orig_x, orig_y = cropped_im.size
        new_x, new_y = size
        if orig_x > orig_y:
            new_x = size[0]
            new_y = math.ceil(size[1] * (orig_y / orig_x))
        elif orig_y > orig_x:
            new_y = size[1]
            new_x = math.ceil(size[0] * (orig_x / orig_y))

        cropped_im = cropped_im.resize(
            size=(new_x - (margin * 2), new_y - (margin * 2)),
            resample=Resampling.BILINEAR,
        )
        bg.paste(
            cropped_im,
            box=(margin, margin + ((size[1] - new_y) // 2)),
        )
        im = bg
        im = apply_overlay_color(im, UiColor.BLUE, theme)

    except OSError as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

    return im


def font_full_preview(filepath: Path, size: tuple[int, int]) -> Image | None:
    """Render a large font preview ("Alphabet") thumbnail from a font file.

    Args:
        filepath (Path): The path of the file.
        size (tuple[int,int]): The size of the thumbnail.
    """
    # Scale the sample font sizes to the preview image
    # resolution,assuming the sizes are tuned for 256px.
    im: Image | None = None
    # TODO: Support for non-square images
    try:
        scaled_sizes: list[int] = [math.floor(x * (size[0] / 256)) for x in FONT_SAMPLE_SIZES]
        bg = new_image("RGBA", size, color="#00000000")
        draw = ImageDraw.Draw(bg)
        lines_of_padding = 2
        y_offset = 0.0

        for font_size in scaled_sizes:
            font = ImageFont.truetype(filepath, size=font_size)
            text_wrapped: str = wrap_full_text(
                FONT_SAMPLE_TEXT, font=font, width=size[0], draw=draw
            )
            draw.multiline_text((0, y_offset), text_wrapped, font=font)
            y_offset += (len(text_wrapped.split("\n")) + lines_of_padding) * draw.textbbox(
                (0, 0), "A", font=font
            )[-1]
        # TODO: Separate from any Qt stuff
        im = auto_theme_overlay(bg, use_alpha=False)
    except OSError as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im
