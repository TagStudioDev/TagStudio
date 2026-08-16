# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from pathlib import Path
from typing import cast

import numpy as np
import structlog
from PIL import Image, ImageDraw, ImageFont

from tagstudio.core.constants import FONT_SAMPLE_SIZES, FONT_SAMPLE_TEXT
from tagstudio.qt.helpers.text_wrapper import wrap_full_text
from tagstudio.qt.views.styles.color_overlay import auto_theme_overlay

logger = structlog.get_logger(__name__)


def font_small_thumb(filepath: Path, size: int) -> Image.Image | None:
    """Render a small font preview ("Aa") thumbnail from a font file.

    Args:
        filepath (Path): The path of the file.
        size (tuple[int,int]): The size of the thumbnail.
    """
    im: Image.Image | None = None
    try:
        bg = Image.new("RGB", (size, size), color="#000000")
        raw = Image.new("RGB", (size * 3, size * 3), color="#000000")
        draw = ImageDraw.Draw(raw)
        font = ImageFont.truetype(filepath, size=size)
        # NOTE: While a stroke effect is desired, the text
        # method only allows for outer strokes, which looks
        # a bit weird when rendering fonts.
        draw.text(
            (size // 8, size // 8),
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
        cropped_im: Image.Image = Image.fromarray(cropped_data, "RGB")

        margin: int = math.ceil(size // 16)

        orig_x, orig_y = cropped_im.size
        new_x, new_y = (size, size)
        if orig_x > orig_y:
            new_x = size
            new_y = math.ceil(size * (orig_y / orig_x))
        elif orig_y > orig_x:
            new_y = size
            new_x = math.ceil(size * (orig_x / orig_y))

        cropped_im = cropped_im.resize(
            size=(new_x - (margin * 2), new_y - (margin * 2)),
            resample=Image.Resampling.BILINEAR,
        )
        bg.paste(
            cropped_im,
            box=(margin, margin + ((size - new_y) // 2)),
        )
        im = bg
    except OSError as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im


def font_full_preview(filepath: Path, size: int) -> Image.Image | None:
    """Render a large font preview ("Alphabet") thumbnail from a font file.

    Args:
        filepath (Path): The path of the file.
        size (tuple[int,int]): The size of the thumbnail.
    """
    # Scale the sample font sizes to the preview image
    # resolution,assuming the sizes are tuned for 256px.
    im: Image.Image | None = None
    try:
        scaled_sizes: list[int] = [math.floor(x * (size / 256)) for x in FONT_SAMPLE_SIZES]
        bg = Image.new("RGBA", (size, size), color="#00000000")
        draw = ImageDraw.Draw(bg)
        lines_of_padding = 2
        y_offset = 0.0

        for font_size in scaled_sizes:
            font = ImageFont.truetype(filepath, size=font_size)
            text_wrapped: str = wrap_full_text(FONT_SAMPLE_TEXT, font=font, width=size, draw=draw)
            draw.multiline_text((0, y_offset), text_wrapped, font=font)
            y_offset += (len(text_wrapped.split("\n")) + lines_of_padding) * draw.textbbox(
                (0, 0), "A", font=font
            )[-1]
        im = auto_theme_overlay(bg, use_alpha=False)
    except OSError as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im
