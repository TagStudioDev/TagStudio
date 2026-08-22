# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from typing import override
from xml.etree.ElementTree import Element

import structlog
from PIL.Image import Image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaCategories
from tagstudio.core.utils.types import unwrap
from tagstudio.previews.base_preview import BasePreview
from tagstudio.previews.renderers.archive import Archive, first_image_in_archive, open_archive
from tagstudio.previews.renderers.raster_image import image_from_bytes

logger = structlog.get_logger(__name__)


class EbookPreview(BasePreview):
    media_type_name = "ebook"
    priority = 40

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
        return epub_thumb(filepath)


def epub_thumb(filepath: Path) -> Image | None:
    """Extracts the cover specified by ComicInfo.xml or first image found in the ePub file.

    Args:
        filepath (Path): The path to the ePub file.
        ext (str): The file extension.

    Returns:
        Image: The cover specified in ComicInfo.xml,
        the first image found in the ePub file, or None by default.
    """
    im: Image | None = None
    try:
        with open_archive(filepath) as archive:
            if "ComicInfo.xml" in archive.namelist():
                comic_info = ET.fromstring(archive.read("ComicInfo.xml"))
                im = cover_from_comic_info(archive, comic_info, "FrontCover")
                if not im:
                    im = cover_from_comic_info(archive, comic_info, "InnerCover")

            if not im:
                im = first_image_in_archive(archive)
    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

    return im


def cover_from_comic_info(archive: Archive, comic_info: Element, cover_type: str) -> Image | None:
    """Extract the cover specified in ComicInfo.xml.

    Args:
        archive (Archive): The current ePub file.
        comic_info (Element): The parsed ComicInfo.xml.
        cover_type (str): The type of cover to load.

    Returns:
        Image: The cover specified in ComicInfo.xml.
    """
    im: Image | None = None

    cover = comic_info.find(f"./*Page[@Type='{cover_type}']")
    if cover is not None:
        pages = [f for f in archive.namelist() if f != "ComicInfo.xml"]  # pyright: ignore[reportUnknownVariableType]
        page_name = pages[int(unwrap(cover.get("Image")))]  # pyright: ignore[reportUnknownVariableType]
        ext = Path(page_name).suffix
        if MediaCategories.IMAGE_RASTER_TYPES.contains(ext):
            image_data = archive.read(page_name)  # pyright: ignore[reportUnknownVariableType]
            im = image_from_bytes(BytesIO(image_data))

    return im
