# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import zipfile
from io import BytesIO
from pathlib import Path

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


def apple_embedded_thumb(filepath: Path) -> Image.Image | None:
    """Extract and render an apple embedded thumbnail (iWork, Apple Creative Studio).

    Args:
        filepath (Path): The path of the file.
    """
    thumb_files: list[str] = [
        "preview.jpg",
        "QuickLook/Preview.heic",
        "QuickLook/Thumbnail.jpg",
        "QuickLook/Thumbnail.heic",
        "QuickLook/Thumbnail.webp",
        "QuickLook/Icon.webp",
    ]
    im: Image.Image | None = None

    def get_image(path: str) -> Image.Image | None:
        thumb_im: Image.Image | None = None
        # Read the specific file into memory
        file_data = zip_file.read(path)
        thumb_im = Image.open(BytesIO(file_data))
        return thumb_im

    try:
        with zipfile.ZipFile(filepath, "r") as zip_file:
            thumb: Image.Image | None = None

            # Check if the file exists in the zip
            for thumb_file in thumb_files:
                if thumb_file in zip_file.namelist():
                    thumb = get_image(thumb_file)
                    break
            else:
                logger.error("Couldn't render thumbnail", filepath=filepath)

            if thumb:
                im = Image.new("RGB", thumb.size, color="#1e1e1e")
                im.paste(thumb)
    except zipfile.BadZipFile as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=e)

    return im
