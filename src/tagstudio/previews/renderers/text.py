# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import io
import textwrap
from math import ceil
from pathlib import Path
from typing import override

import structlog
from PIL import ImageFont, UnidentifiedImageError
from PIL.Image import DecompressionBombError, Image, Resampling
from PIL.Image import new as new_image
from PIL.Image import open as open_image
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import PythonLexer
from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    Other,
    Punctuation,
    String,
    Text,
)

from tagstudio.core.enums import Theme
from tagstudio.core.utils.encoding import detect_char_encoding
from tagstudio.previews.base_preview import BasePreview

logger = structlog.get_logger(__name__)


class TextLightStyle(Style):
    background = "#FFFFFF"
    foreground = "#000000"

    background_color = background
    styles = {
        Generic: foreground + " bold",
        Text: foreground + " bold",
        Literal: foreground + " bold",
        String: foreground + " bold",
    }


class TextDarkStyle(Style):
    background = "#111111"
    foreground = "#FFFFFF"

    background_color = background
    styles = {
        Generic: foreground,
        Text: foreground,
        Literal: foreground,
        String: foreground,
        Comment: foreground,
        Error: foreground,
        Keyword: foreground,
        Name: foreground,
        Number: foreground,
        Operator: foreground,
        Other: foreground,
        Punctuation: foreground,
    }


class TextPreview(BasePreview):
    media_type_name = "plaintext"
    font = ImageFont.load_default(20)

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
        return text_thumb(
            filepath=filepath,
            size=size,
            style=TextDarkStyle if theme == Theme.DARK else TextLightStyle,
        )


def text_thumb(
    filepath: Path,
    size: tuple[int, int],
    style: type[Style],
) -> Image | None:
    """Render a thumbnail for a plaintext file.

    Args:
        filepath (Path): The path of the file.
        size (str): The final size for the image.
        style (str): The pygments style class to use.
    """
    im: Image | None = None

    try:
        encoding: str = detect_char_encoding(filepath) or "UTF-8"
        with open(filepath, encoding=encoding) as text_file:
            text = text_file.read(1024)

        wrapped_text = "\n".join(
            "\n".join(textwrap.wrap(line, width=40)) for line in text.splitlines()
        )

        # TODO: Get this path from the ResourceManager, when that can handle fonts.
        font_path = str(
            Path(__file__).parents[2] / "resources/fonts/JetBrainsMono/JetBrainsMono.ttf"
        )
        # logger.info(font_path)

        image_bytes = highlight(
            wrapped_text,
            PythonLexer(),
            ImageFormatter(
                encoding=encoding,
                font_name=font_path,
                font_size=32,
                line_numbers=False,
                style=style,
                image_pad=48,
            ),
        )
        im_text = open_image(io.BytesIO(image_bytes))

        ratio_w = size[0] / im_text.width
        im_text = Image.resize(
            im_text,
            (ceil(im_text.width * ratio_w), ceil(im_text.height * ratio_w)),
            Resampling.BILINEAR,
        )

        bg = new_image("RGB", size, color=style.background_color)
        Image.paste(bg, im_text, (0, 0))

        return bg

    except (
        UnidentifiedImageError,
        DecompressionBombError,
        UnicodeDecodeError,
        OSError,
        FileNotFoundError,
    ) as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=e)
    return im
