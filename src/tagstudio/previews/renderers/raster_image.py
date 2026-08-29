# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import os
from io import BytesIO
from pathlib import Path
from typing import override

import cv2
import numpy as np
import structlog
from PIL import ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError, Image, fromarray
from PIL.Image import new as new_image
from PIL.Image import open as open_image
from pillow_heif import register_heif_opener  # pyright: ignore[reportUnknownVariableType]

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.core.utils.types import unwrap
from tagstudio.previews.base_preview import RENDER, BasePreview

logger = structlog.get_logger(__name__)

try:
    import pillow_jxl  # noqa: F401 # pyright: ignore
except ImportError as e:
    logger.error('[ThumbRenderer] Could not import the "pillow_jxl" module', error=e)

register_heif_opener()
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

# NOTE: Filetype equivalents (i.e. ".jpg" == ".jpeg") are already declared internally.
MediaTypes.register("image.raster", ".apng", RENDER)
MediaTypes.register("image.raster", ".avif", RENDER)
MediaTypes.register("image.raster", ".bmp", RENDER)
MediaTypes.register("image.raster", ".png", RENDER)
MediaTypes.register("image.raster", ".exr", RENDER)
MediaTypes.register("image.raster", ".gif", RENDER)
MediaTypes.register("image.raster", ".jxl", RENDER)
MediaTypes.register("image.raster", ".psd", RENDER)
MediaTypes.register("image.raster", ".webp", RENDER)
MediaTypes.register("image.raster", ".heif", RENDER)
MediaTypes.register("image.raster", ".jpg2", RENDER)
MediaTypes.register("image.raster", ".jpeg", RENDER)
MediaTypes.register("image.raster", ".tiff", RENDER)


class RasterImagePreview(BasePreview):
    media_type_name = "image.raster"

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
        return raster_image_thumb(filepath)


def raster_image_thumb(filepath: Path) -> Image | None:
    """Render a thumbnail for a standard image type.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image | None = None
    try:
        if filepath.suffix.lower() == ".exr":
            return exr_image_thumb(filepath)

        with filepath.open("rb") as file:
            im = image_from_bytes(BytesIO(file.read()))
    except (
        DecompressionBombError,
        FileNotFoundError,
        NotImplementedError,
        OSError,
        UnidentifiedImageError,
    ) as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im


def exr_image_thumb(filepath: Path) -> Image | None:
    """Render a thumbnail for a EXR image type.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image | None = None
    try:
        # Load the EXR data to an array and rotate the color space from BGRA -> RGBA
        raw_array = cv2.imread(str(filepath), cv2.IMREAD_UNCHANGED)
        assert raw_array is not None
        raw_array[..., :3] = raw_array[..., 2::-1]

        # Correct the gamma of the raw array
        gamma = 2.2
        array_gamma = np.power(np.clip(raw_array, 0, 1), 1 / gamma)
        array = (array_gamma * 255).astype(np.uint8)

        im = fromarray(array, mode="RGBA")

        # Paste solid background
        if im.mode == "RGBA":
            new_bg = new_image("RGB", im.size, color="#1e1e1e")
            new_bg.paste(im, mask=im.getchannel(3))
            im = new_bg

    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im


def image_from_bytes(image_data: BytesIO) -> Image:
    """Load a raster image and add a background if it's transparent.

    Args:
        image_data (BytesIO): The binary image data.

    Returns:
        Image.Image: The loaded raster image, with a background if needed.
    """
    im: Image = open_image(image_data)
    if im.mode != "RGB" and im.mode != "RGBA":
        im = im.convert(mode="RGBA")
    if im.mode == "RGBA":
        new_bg = new_image("RGB", im.size, color="#1e1e1e")
        new_bg.paste(im, mask=im.getchannel(3))
        im = new_bg
    return unwrap(ImageOps.exif_transpose(im))
