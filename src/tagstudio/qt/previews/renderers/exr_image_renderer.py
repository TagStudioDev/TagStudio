from pathlib import Path

import Imath
import numexpr
import numpy
import OpenEXR
import structlog
from PIL import (
    Image,
    ImageOps,
)

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class EXRImageRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Render a thumbnail for an EXR image file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            rendered_image: Image.Image = exr_to_srgb(context.path)
            return unwrap(ImageOps.exif_transpose(rendered_image))
        except Exception as e:
            logger.error("[EXRImageRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None


# https://gist.github.com/arseniy-panfilov/4dc8fc5131277affe64619b1a9d00da0
FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)


def exr_to_array(path: Path):
    exr_file = OpenEXR.InputFile(path.as_posix())
    data_window = exr_file.header()["dataWindow"]

    channels = list(exr_file.header()["channels"].keys())
    channels_list = [c for c in ("R", "G", "B", "A") if c in channels]
    size = (data_window.max.x - data_window.min.x + 1, data_window.max.y - data_window.min.y + 1)

    color_channels = exr_file.channels(channels_list, FLOAT)
    channels_tuple = [numpy.frombuffer(channel, dtype="f") for channel in color_channels]

    return numpy.dstack(channels_tuple).reshape(size + (len(channels_tuple),))


def encode_to_srgb(x):
    a = 0.055  # noqa
    return numexpr.evaluate("""where(
        x <= 0.0031308,
        x * 12.92,
        (1 + a) * (x ** (1 / 2.4)) - a
    )""")


def exr_to_srgb(exr_file):
    array = exr_to_array(exr_file)
    result = encode_to_srgb(array) * 255.0
    present_channels = ["R", "G", "B", "A"][: result.shape[2]]
    channels = "".join(present_channels)
    return Image.fromarray(result.astype("uint8"), channels)
