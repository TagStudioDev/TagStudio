# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import base64
import struct
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image
from PIL.Image import new as new_image
from PIL.Image import open as open_image

from tagstudio.core.enums import Theme
from tagstudio.previews.base_preview import BasePreview

logger = structlog.get_logger(__name__)


class PaintDotNetPreview(BasePreview):
    media_type_name = "paint_dot_net"

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
        return paint_dot_net_thumb(filepath)


def paint_dot_net_thumb(filepath: Path) -> Image | None:
    """Extract the base64-encoded thumbnail from a .pdn file header.

    Args:
        filepath (Path): The path of the .pdn file.

    Returns:
        Image: the decoded PNG thumbnail or None by default.
    """
    im: Image | None = None
    with open(filepath, "rb") as f:
        try:
            # First 4 bytes are the magic number
            if f.read(4) != b"PDN3":
                return im

            # Header length is a little-endian 24-bit int
            header_size = struct.unpack("<i", f.read(3) + b"\x00")[0]
            thumb_element = ET.fromstring(f.read(header_size)).find("./*thumb")
            if thumb_element is None:
                return im

            encoded_png = thumb_element.get("png")
            if encoded_png:
                decoded_png = base64.b64decode(encoded_png)
                im = open_image(BytesIO(decoded_png))
                if im.mode == "RGBA":
                    new_bg = new_image("RGB", im.size, color="#1e1e1e")
                    new_bg.paste(im, mask=im.getchannel(3))
                    im = new_bg
        except Exception as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

    return im
