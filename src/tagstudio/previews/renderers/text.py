# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

import cv2
import structlog
from PIL import Image, ImageDraw, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from tagstudio.core.utils.encoding import detect_char_encoding

logger = structlog.get_logger(__name__)


def text_thumb(filepath: Path) -> Image.Image | None:
    """Render a thumbnail for a plaintext file.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image.Image | None = None

    bg_color: str = (
        "#1e1e1e"
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else "#FFFFFF"
    )
    fg_color: str = (
        "#FFFFFF"
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else "#111111"
    )

    try:
        encoding = detect_char_encoding(filepath)
        with open(filepath, encoding=encoding) as text_file:
            text = text_file.read(256)
        bg = Image.new("RGB", (256, 256), color=bg_color)
        draw = ImageDraw.Draw(bg)
        draw.text((16, 16), text, fill=fg_color)
        im = bg
    except (
        UnidentifiedImageError,
        cv2.error,
        DecompressionBombError,
        UnicodeDecodeError,
        OSError,
        FileNotFoundError,
    ) as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im
