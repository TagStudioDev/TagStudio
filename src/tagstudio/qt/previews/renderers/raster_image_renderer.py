import structlog
from PIL import (
    Image,
    ImageOps,
    UnidentifiedImageError,
)
from PIL.Image import DecompressionBombError

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class RasterImageRenderer(BaseRenderer):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for an image file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            rendered_image: Image.Image = Image.open(context.path)

            # Convert image to RGBA
            if rendered_image.mode != "RGB" and rendered_image.mode != "RGBA":
                rendered_image = rendered_image.convert(mode="RGBA")

            if rendered_image.mode == "RGBA":
                new_bg: Image.Image = Image.new("RGB", rendered_image.size, color="#1e1e1e")
                new_bg.paste(rendered_image, mask=rendered_image.getchannel(3))
                rendered_image = new_bg

            return unwrap(ImageOps.exif_transpose(rendered_image))
        except (
            FileNotFoundError,
            UnidentifiedImageError,
            DecompressionBombError,
            NotImplementedError,
        ) as e:
            logger.error("[ImageRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
