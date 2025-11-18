import math
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
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class FontRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for a plaintext file.

        Args:
            context (RendererContext): The renderer context.
        """
        if context.is_grid_thumb:
            return FontRenderer._font_short_thumb(context)
        else:
            return FontRenderer._font_long_thumb(context)

    @staticmethod
    def _font_short_thumb(context: RendererContext) -> Image.Image | None:
        """Render a small font preview ("Aa") thumbnail from a font file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            bg = Image.new("RGB", (context.size, context.size), color="#000000")
            raw = Image.new("RGB", (context.size * 3, context.size * 3), color="#000000")
            draw = ImageDraw.Draw(raw)
            font = ImageFont.truetype(context.path, size=context.size)

            # NOTE: While a stroke effect is desired, the text
            # method only allows for outer strokes, which looks
            # a bit weird when rendering fonts.
            draw.text(
                (context.size // 8, context.size // 8),
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

            margin: int = math.ceil(context.size // 16)

            orig_x, orig_y = cropped_image.size
            new_x, new_y = (context.size, context.size)
            if orig_x > orig_y:
                new_x = context.size
                new_y = math.ceil(context.size * (orig_y / orig_x))
            elif orig_y > orig_x:
                new_y = context.size
                new_x = math.ceil(context.size * (orig_x / orig_y))

            cropped_image = cropped_image.resize(
                size=(new_x - (margin * 2), new_y - (margin * 2)),
                resample=Image.Resampling.BILINEAR,
            )
            bg.paste(
                cropped_image,
                box=(margin, margin + ((context.size - new_y) // 2)),
            )
            return apply_overlay_color(bg, UiColor.BLUE)
        except OSError as e:
            logger.error("Couldn't render thumbnail", path=context.path, error=type(e).__name__)

        return None

    @staticmethod
    def _font_long_thumb(context: RendererContext) -> Image.Image | None:
        """Render a large font preview ("Alphabet") thumbnail from a font file.

        Args:
            context (RendererContext): The renderer context.
        """
        # Scale the sample font sizes to the preview image
        # resolution,assuming the sizes are tuned for 256px.
        try:
            scaled_sizes: list[int] = [
                math.floor(x * (context.size / 256)) for x in FONT_SAMPLE_SIZES
            ]
            bg = Image.new("RGBA", (context.size, context.size), color="#00000000")
            draw = ImageDraw.Draw(bg)
            lines_of_padding = 2
            y_offset = 0.0

            for font_size in scaled_sizes:
                font = ImageFont.truetype(context.path, size=font_size)
                text_wrapped: str = wrap_full_text(
                    FONT_SAMPLE_TEXT,
                    font=font,  # pyright: ignore[reportArgumentType]
                    width=context.size,
                    draw=draw,
                )
                draw.multiline_text((0, y_offset), text_wrapped, font=font)
                y_offset += (len(text_wrapped.split("\n")) + lines_of_padding) * draw.textbbox(
                    (0, 0), "A", font=font
                )[-1]
            return theme_fg_overlay(bg, use_alpha=False)
        except OSError as e:
            logger.error("[FontRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
