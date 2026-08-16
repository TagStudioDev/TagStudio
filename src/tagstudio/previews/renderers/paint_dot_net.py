# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import base64
import struct
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


def paint_dot_net_thumb(filepath: Path) -> Image.Image | None:
    """Extract the base64-encoded thumbnail from a .pdn file header.

    Args:
        filepath (Path): The path of the .pdn file.

    Returns:
        Image: the decoded PNG thumbnail or None by default.
    """
    im: Image.Image | None = None
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
                im = Image.open(BytesIO(decoded_png))
                if im.mode == "RGBA":
                    new_bg = Image.new("RGB", im.size, color="#1e1e1e")
                    new_bg.paste(im, mask=im.getchannel(3))
                    im = new_bg
        except Exception as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

    return im
