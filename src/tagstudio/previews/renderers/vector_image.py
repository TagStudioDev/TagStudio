# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# NOTE: This file contains Qt imports because Qt is used as the vector renderer in this case.
# This is NOT considered part of the Qt frontend, but is technically tangled with the Qt import.

from io import BytesIO
from pathlib import Path
from typing import override

import structlog
from PIL import UnidentifiedImageError
from PIL.Image import Image
from PIL.Image import new as new_image
from PIL.Image import open as open_image
from PySide6.QtCore import QBuffer, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from tagstudio.core.enums import Theme
from tagstudio.previews.base_preview import BasePreview

logger = structlog.get_logger(__name__)


class VectorImagePreview(BasePreview):
    media_type_name = "image.vector"
    priority = 70

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
        return vector_image_thumb(filepath, size)


def vector_image_thumb(filepath: Path, size: tuple[int, int]) -> Image:
    """Render a thumbnail for a vector image, such as SVG.

    Args:
        filepath (Path): The path of the file.
        size (tuple[int,int]): The size of the thumbnail.
    """
    im: Image | None = None
    # Create an image to draw the svg to and a painter to do the drawing
    q_image: QImage = QImage(size[0], size[1], QImage.Format.Format_ARGB32)
    q_image.fill("#1e1e1e")

    # Create an svg renderer, then render to the painter
    svg: QSvgRenderer = QSvgRenderer(str(filepath))

    if not svg.isValid():
        raise UnidentifiedImageError

    painter: QPainter = QPainter(q_image)
    svg.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
    svg.render(painter)
    painter.end()

    # Write the image to a buffer as png
    buffer: QBuffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    q_image.save(buffer, "PNG")  # pyright: ignore[reportCallIssue, reportArgumentType]

    # Load the image from the buffer
    im = new_image("RGB", size, color="#1e1e1e")
    im.paste(open_image(BytesIO(buffer.data().data())))
    im = im.convert(mode="RGB")

    buffer.close()
    return im
