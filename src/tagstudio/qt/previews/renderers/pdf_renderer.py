from io import BytesIO

import structlog
from PIL import (
    Image,
)
from PySide6.QtCore import QBuffer, QFile, QFileDevice, QIODeviceBase, QSizeF
from PySide6.QtGui import QImage
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions

from tagstudio.qt.helpers.image_effects import replace_transparent_pixels
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class PDFRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for a PDF file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            file: QFile = QFile(context.path)
            success: bool = file.open(
                QIODeviceBase.OpenModeFlag.ReadOnly, QFileDevice.Permission.ReadUser
            )

            if not success:
                raise FileNotFoundError

            document: QPdfDocument = QPdfDocument()
            document.load(file)
            file.close()

            # Transform page_size in points to pixels with proper aspect ratio
            page_size: QSizeF = document.pagePointSize(0)
            ratio_hw: float = page_size.height() / page_size.width()
            if ratio_hw >= 1:
                page_size *= context.size / page_size.height()
            else:
                page_size *= context.size / page_size.width()

            # Enlarge image for antialiasing
            scale_factor = 2.5
            page_size *= scale_factor

            # Render image with no antialiasing for speed
            render_options: QPdfDocumentRenderOptions = QPdfDocumentRenderOptions()
            render_options.setRenderFlags(QPdfDocumentRenderOptions.RenderFlag.TextAliased)

            # Convert QImage to PIL Image
            q_image: QImage = document.render(0, page_size.toSize(), render_options)
            buffer: QBuffer = QBuffer()
            buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            try:
                q_image.save(buffer, "PNG")  # type: ignore[unused-ignore] # pyright: ignore
                rendered_thumbnail = Image.open(BytesIO(buffer.buffer().data()))
            finally:
                buffer.close()
            # Replace transparent pixels with white (otherwise Background defaults to transparent)
            return replace_transparent_pixels(rendered_thumbnail)

        except FileNotFoundError as e:
            logger.error("[AudioRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
