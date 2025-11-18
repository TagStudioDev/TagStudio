import cv2
import numpy as np
import structlog
from PIL import (
    Image,
)

from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class EXRImageRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for a RAW image file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            # Load the EXR data to an array and rotate the color space from BGRA -> RGBA
            raw_array = cv2.imread(str(context.path), cv2.IMREAD_UNCHANGED)
            raw_array[..., :3] = raw_array[..., 2::-1]

            # Correct the gamma of the raw array
            gamma = 2.2
            array_gamma = np.power(np.clip(raw_array, 0, 1), 1 / gamma)
            array = (array_gamma * 255).astype(np.uint8)

            rendered_image: Image.Image = Image.fromarray(array, mode="RGBA")

            # Paste solid background
            if rendered_image.mode == "RGBA":
                new_bg = Image.new("RGB", rendered_image.size, color="#1e1e1e")
                new_bg.paste(rendered_image, mask=rendered_image.getchannel(3))
                return new_bg
        except Exception as e:
            logger.error("[EXRImageRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
