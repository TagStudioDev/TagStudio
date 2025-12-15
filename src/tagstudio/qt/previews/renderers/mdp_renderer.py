import os
import struct
import xml.etree.ElementTree as ElementTree
import zlib

import structlog
from PIL import Image

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)

thumbnail_path_within_zip: str = "preview.png"


class MDIPackRenderer(BaseRenderer):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Extract and render a thumbnail for a .mdp file.

        Args:
            context (RendererContext): The renderer context.
        """
        try:
            with open(context.path, "rb") as mdp_file:
                magic = struct.unpack("<7sx", mdp_file.read(8))[0]
                if magic != b"mdipack":
                    return None

                bin_header = struct.unpack("<LLL", mdp_file.read(12))
                xml_header = ElementTree.fromstring(mdp_file.read(bin_header[1]))
                mdibin_count = len(xml_header.findall("./*Layer")) + 1

                for _ in range(mdibin_count):
                    pac_header = struct.unpack("<3sxLLLL48s64s", mdp_file.read(132))
                    if not pac_header[6].startswith(b"thumb"):
                        mdp_file.seek(pac_header[3], os.SEEK_CUR)
                        continue

                    thumb_element = unwrap(xml_header.find("Thumb"))
                    dimensions = (
                        int(unwrap(thumb_element.get("width"))),
                        int(unwrap(thumb_element.get("height"))),
                    )
                    thumb_blob = mdp_file.read(pac_header[3])
                    if pac_header[2] == 1:
                        thumb_blob = zlib.decompress(thumb_blob, bufsize=pac_header[4])

                    return Image.frombytes("RGBA", dimensions, thumb_blob, "raw", "BGRA")
        except Exception as e:
            logger.error("[MDIPackRenderer] Couldn't render thumbnail", path=context.path, error=e)

        return None
