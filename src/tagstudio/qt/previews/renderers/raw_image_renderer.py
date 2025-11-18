import rawpy
import structlog
from PIL import (
    Image,
)
from PIL.Image import DecompressionBombError
from rawpy._rawpy import LibRawFileUnsupportedError, LibRawIOError

from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class RawImageRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for a RAW image file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            with rawpy.imread(str(context.path)) as raw:
                rgb = raw.postprocess(use_camera_wb=True)
                rendered_image = Image.frombytes(
                    "RGB",
                    (rgb.shape[1], rgb.shape[0]),
                    rgb,
                    decoder_name="raw",
                )
                return rendered_image
        except (DecompressionBombError, LibRawIOError, LibRawFileUnsupportedError) as e:
            logger.error("[RawImageRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
