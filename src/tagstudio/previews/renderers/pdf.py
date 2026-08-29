# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# NOTE: This file contains Qt imports because Qt is used as the vector renderer in this case.
# This is NOT considered part of the Qt frontend, but is technically tangled with the Qt import.


from io import BytesIO
from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image
from PIL.Image import open as open_image
from PySide6.QtCore import QBuffer, QFile, QFileDevice, QIODeviceBase, QSizeF
from PySide6.QtGui import QImage
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.qt.views.styles.image_effects import replace_transparent_pixels

logger = structlog.get_logger(__name__)

MediaTypes.register("pdf", ".pdf", RENDER)
MediaTypes.register("pdf", ".ai", RENDER)


class PdfPreview(BasePreview):
    media_type_name = "pdf"

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
        return pdf_thumb(filepath, size)


def pdf_thumb(filepath: Path, size: tuple[int, int]) -> Image | None:
    """Render a thumbnail for a PDF or Adobe Illustrator file.

    filepath (Path): The path of the file.
        size (int): The size of the icon.
        ext (str): The file extension.
    """
    im: Image | None = None

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
    # TODO: Make compatible with non-square images
    if ratio_hw >= 1:
        page_size *= size[0] / page_size.height()
    else:
        page_size *= size[0] / page_size.width()
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
        im = open_image(BytesIO(buffer.buffer().data()))
    finally:
        buffer.close()
    # Replace transparent pixels with white (otherwise Background defaults to transparent)
    return replace_transparent_pixels(im)
