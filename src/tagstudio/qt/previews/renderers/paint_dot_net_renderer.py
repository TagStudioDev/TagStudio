import base64
import struct
import xml.etree.ElementTree as ElementTree
from io import BytesIO

import structlog
from PIL import Image

from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)

thumbnail_path_within_zip: str = "preview.png"


class PaintDotNetRenderer(BaseRenderer):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Extract and render a thumbnail for a Paint.NET file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            with open(context.path, "rb") as pdn_file:
                # Check that first 4 bytes are the magic number
                if pdn_file.read(4) != b"PDN3":
                    return None

                # Header length is a little-endian 24-bit int
                header_size = struct.unpack("<i", pdn_file.read(3) + b"\x00")[0]
                thumb_element = ElementTree.fromstring(pdn_file.read(header_size)).find("./*thumb")
                if thumb_element is None:
                    return None

                encoded_png = thumb_element.get("png")
                if encoded_png:
                    decoded_png = base64.b64decode(encoded_png)
                    decoded_thumbnail = Image.open(BytesIO(decoded_png))
                    if decoded_thumbnail.mode == "RGBA":
                        rendered_thumbnail = Image.new(
                            "RGB", decoded_thumbnail.size, color="#1e1e1e"
                        )
                        rendered_thumbnail.paste(
                            decoded_thumbnail, mask=decoded_thumbnail.getchannel(3)
                        )
                        return rendered_thumbnail

        except Exception as e:
            logger.error(
                "[PaintDotNetRenderer] Couldn't render thumbnail", path=context.path, error=e
            )

        return None
