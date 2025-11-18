from io import BytesIO

import structlog
from PIL import (
    Image,
    UnidentifiedImageError,
)
from PySide6.QtCore import QBuffer, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class VectorImageRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for a vector image, such as SVG.

        Args:
            context (RendererContext): The renderer context.
        """
        # Create an image to draw the svg to and a painter to do the drawing
        q_image: QImage = QImage(context.size, context.size, QImage.Format.Format_ARGB32)
        q_image.fill("#1e1e1e")

        # Create an svg renderer, then render to the painter
        svg: QSvgRenderer = QSvgRenderer(str(context.path))

        if not svg.isValid():
            raise UnidentifiedImageError

        painter: QPainter = QPainter(q_image)
        svg.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        svg.render(painter)
        painter.end()

        # Write the image to a buffer as png
        buffer: QBuffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        q_image.save(buffer, "PNG")  # type: ignore[call-overload,unused-ignore]

        # Load the image from the buffer
        rendered_image: Image.Image = Image.new(
            "RGB", (context.size, context.size), color="#1e1e1e"
        )
        rendered_image.paste(Image.open(BytesIO(buffer.data().data())))
        rendered_image = rendered_image.convert(mode="RGB")

        buffer.close()
        return rendered_image
