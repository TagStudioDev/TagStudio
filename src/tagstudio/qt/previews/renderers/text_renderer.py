from pathlib import Path

import cv2
import structlog
from PIL import (
    Image,
    ImageDraw,
    UnidentifiedImageError,
)
from PIL.Image import DecompressionBombError
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from tagstudio.core.utils.encoding import detect_char_encoding
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer

logger = structlog.get_logger(__name__)


class TextRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(path: Path, extension: str) -> Image.Image | None:
        """Render a thumbnail for a plaintext file.

        Args:
            path (Path): The path of the file.
            extension (str): The file extension.
        """
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
            # Read text file
            encoding = detect_char_encoding(path)
            with open(path, encoding=encoding) as text_file:
                text = text_file.read(256)

            rendered_image = Image.new("RGB", (256, 256), color=bg_color)
            draw = ImageDraw.Draw(rendered_image)
            draw.text((16, 16), text, fill=fg_color)
            return rendered_image
        except (
            UnidentifiedImageError,
            cv2.error,
            DecompressionBombError,
            UnicodeDecodeError,
            OSError,
            FileNotFoundError,
        ) as e:
            logger.error("Couldn't render thumbnail", path=path, error=e)

        return None
