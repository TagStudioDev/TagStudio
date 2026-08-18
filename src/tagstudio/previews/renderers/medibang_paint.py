# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import os
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

import structlog
from PIL import Image

from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger(__name__)


def medibang_paint_thumb(filepath: Path) -> Image.Image | None:
    """Extract the thumbnail from a .mdp file.

    Args:
        filepath (Path): The path of the .mdp file.

    Returns:
        Image: The embedded thumbnail.
    """
    im: Image.Image | None = None
    try:
        with open(filepath, "rb") as f:
            magic = struct.unpack("<7sx", f.read(8))[0]
            if magic != b"mdipack":
                return im

            bin_header = struct.unpack("<LLL", f.read(12))
            xml_header = ET.fromstring(f.read(bin_header[1]))
            mdibin_count = len(xml_header.findall("./*Layer")) + 1
            for _ in range(mdibin_count):
                pac_header = struct.unpack("<3sxLLLL48s64s", f.read(132))
                if not pac_header[6].startswith(b"thumb"):
                    f.seek(pac_header[3], os.SEEK_CUR)
                    continue

                thumb_element = unwrap(xml_header.find("Thumb"))
                dimensions = (
                    int(unwrap(thumb_element.get("width"))),
                    int(unwrap(thumb_element.get("height"))),
                )
                thumb_blob = f.read(pac_header[3])
                if pac_header[2] == 1:
                    thumb_blob = zlib.decompress(thumb_blob, bufsize=pac_header[4])

                im = Image.frombytes("RGBA", dimensions, thumb_blob, "raw", "BGRA")
                break
    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

    return im
