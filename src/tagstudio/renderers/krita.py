# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import zipfile
from io import BytesIO
from pathlib import Path

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


def krita_thumb(filepath: Path) -> Image.Image | None:
    """Extract and render a thumbnail for a Krita file.

    Args:
        filepath (Path): The path of the file.
    """
    file_path_within_zip = "preview.png"
    im: Image.Image | None = None
    with zipfile.ZipFile(filepath, "r") as zip_file:
        # Check if the file exists in the zip
        if file_path_within_zip in zip_file.namelist():
            # Read the specific file into memory
            file_data = zip_file.read(file_path_within_zip)
            thumb_im = Image.open(BytesIO(file_data))
            if thumb_im:
                im = Image.new("RGB", thumb_im.size, color="#1e1e1e")
                im.paste(thumb_im)
        else:
            logger.error("Couldn't render thumbnail", filepath=filepath)

    return im
