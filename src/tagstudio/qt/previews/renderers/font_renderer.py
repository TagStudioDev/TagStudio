import math
from pathlib import Path
from typing import cast

import numpy as np
import structlog
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)

from tagstudio.core.constants import FONT_SAMPLE_SIZES, FONT_SAMPLE_TEXT
from tagstudio.qt.helpers.color_overlay import theme_fg_overlay
from tagstudio.qt.helpers.image_effects import apply_overlay_color
from tagstudio.qt.helpers.text_wrapper import wrap_full_text
from tagstudio.qt.models.palette import UiColor
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer

logger = structlog.get_logger(__name__)


class FontRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(path: Path, extension: str, size: int, is_grid_thumb: bool) -> Image.Image | None:
        """Render a thumbnail for a plaintext file.

        Args:
            path (Path): The path of the file.
            extension (str): The file extension.
            size (tuple[int,int]): The size of the thumbnail.
            is_grid_thumb (bool): Whether the image will be used as a thumbnail in the file grid.
        """
        if is_grid_thumb:
            return FontRenderer._font_short_thumb(path, size)
        else:
            return FontRenderer._font_long_thumb(path, size)

    @staticmethod
    def _font_short_thumb(path: Path, size: int) -> Image.Image | None:
        """Render a small font preview ("Aa") thumbnail from a font file.

        Args:
            path (Path): The path of the file.
            size (tuple[int,int]): The size of the thumbnail.
        """
        try:
            bg = Image.new("RGB", (size, size), color="#000000")
            raw = Image.new("RGB", (size * 3, size * 3), color="#000000")
            draw = ImageDraw.Draw(raw)
            font = ImageFont.truetype(path, size=size)

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
            cropped_image: Image.Image = Image.fromarray(cropped_data, "RGB")

            margin: int = math.ceil(size // 16)

            orig_x, orig_y = cropped_image.size
            new_x, new_y = (size, size)
            if orig_x > orig_y:
                new_x = size
                new_y = math.ceil(size * (orig_y / orig_x))
            elif orig_y > orig_x:
                new_y = size
                new_x = math.ceil(size * (orig_x / orig_y))

            cropped_image = cropped_image.resize(
                size=(new_x - (margin * 2), new_y - (margin * 2)),
                resample=Image.Resampling.BILINEAR,
            )
            bg.paste(
                cropped_image,
                box=(margin, margin + ((size - new_y) // 2)),
            )
            return apply_overlay_color(bg, UiColor.BLUE)
        except OSError as e:
            logger.error("Couldn't render thumbnail", path=path, error=type(e).__name__)

        return None

    @staticmethod
    def _font_long_thumb(path: Path, size: int) -> Image.Image | None:
        """Render a large font preview ("Alphabet") thumbnail from a font file.

        Args:
            path (Path): The path of the file.
            size (tuple[int,int]): The size of the thumbnail.
        """
        # Scale the sample font sizes to the preview image
        # resolution,assuming the sizes are tuned for 256px.
        try:
            scaled_sizes: list[int] = [math.floor(x * (size / 256)) for x in FONT_SAMPLE_SIZES]
            bg = Image.new("RGBA", (size, size), color="#00000000")
            draw = ImageDraw.Draw(bg)
            lines_of_padding = 2
            y_offset = 0.0

            for font_size in scaled_sizes:
                font = ImageFont.truetype(path, size=font_size)
                text_wrapped: str = wrap_full_text(
                    FONT_SAMPLE_TEXT,
                    font=font,  # pyright: ignore[reportArgumentType]
                    width=size,
                    draw=draw,
                )
                draw.multiline_text((0, y_offset), text_wrapped, font=font)
                y_offset += (len(text_wrapped.split("\n")) + lines_of_padding) * draw.textbbox(
                    (0, 0), "A", font=font
                )[-1]
            return theme_fg_overlay(bg, use_alpha=False)
        except OSError as e:
            logger.error("[FontRenderer] Couldn't render thumbnail", path=path, error=e)

        return None
