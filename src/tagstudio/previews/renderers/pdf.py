# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# NOTE: This file contains Qt imports because Qt is used as the vector renderer in this case.
# This is NOT considered part of the Qt frontend, but is technically tangled with the Qt import.


from io import BytesIO
from pathlib import Path

import structlog
from PIL import Image
from PySide6.QtCore import QBuffer, QFile, QFileDevice, QIODeviceBase, QSizeF
from PySide6.QtGui import QImage
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions

from tagstudio.qt.views.styles.image_effects import replace_transparent_pixels

logger = structlog.get_logger(__name__)


def pdf_thumb(filepath: Path, size: int) -> Image.Image | None:
    """Render a thumbnail for a PDF or Adobe Illustrator file.

    filepath (Path): The path of the file.
        size (int): The size of the icon.
        ext (str): The file extension.
    """
    im: Image.Image | None = None

    file: QFile = QFile(filepath)
    success: bool = file.open(QIODeviceBase.OpenModeFlag.ReadOnly, QFileDevice.Permission.ReadUser)
    if not success:
        logger.error("Couldn't render thumbnail", filepath=filepath)
        return im
    document: QPdfDocument = QPdfDocument()
    document.load(file)
    file.close()
    # Transform page_size in points to pixels with proper aspect ratio
    page_size: QSizeF = document.pagePointSize(0)
    ratio_hw: float = page_size.height() / page_size.width()
    if ratio_hw >= 1:
        page_size *= size / page_size.height()
    else:
        page_size *= size / page_size.width()
    # Enlarge image for anti-aliasing
    scale_factor = 2.5
    page_size *= scale_factor
    # Render image with no anti-aliasing for speed
    render_options: QPdfDocumentRenderOptions = QPdfDocumentRenderOptions()
    render_options.setRenderFlags(
        QPdfDocumentRenderOptions.RenderFlag.TextAliased
        | QPdfDocumentRenderOptions.RenderFlag.ImageAliased
        | QPdfDocumentRenderOptions.RenderFlag.PathAliased
    )
    # Convert QImage to PIL Image
    q_image: QImage = document.render(0, page_size.toSize(), render_options)
    buffer: QBuffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    try:
        q_image.save(buffer, "PNG")  # pyright: ignore
        im = Image.open(BytesIO(buffer.buffer().data()))
    finally:
        buffer.close()
    # Replace transparent pixels with white (otherwise Background defaults to transparent)
    return replace_transparent_pixels(im)
