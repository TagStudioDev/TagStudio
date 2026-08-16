# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import os
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import rawpy
import structlog
from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from pillow_heif import register_heif_opener  # pyright: ignore[reportUnknownVariableType]
from rawpy import (
    LibRawFileUnsupportedError,  # pyright: ignore[reportPrivateImportUsage]
    LibRawIOError,  # pyright: ignore[reportPrivateImportUsage]
)

from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger(__name__)

try:
    import pillow_jxl  # noqa: F401 # pyright: ignore
except ImportError as e:
    logger.error('[ThumbRenderer] Could not import the "pillow_jxl" module', error=e)

register_heif_opener()
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"


def raster_image_thumb(filepath: Path) -> Image.Image | None:
    """Render a thumbnail for a standard image type.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image.Image | None = None
    try:
        with filepath.open("rb") as file:
            im = image_from_bytes(BytesIO(file.read()))
    except (
        FileNotFoundError,
        UnidentifiedImageError,
        DecompressionBombError,
        NotImplementedError,
    ) as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im


def exr_image_thumb(filepath: Path) -> Image.Image | None:
    """Render a thumbnail for a EXR image type.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image.Image | None = None
    try:
        # Load the EXR data to an array and rotate the color space from BGRA -> RGBA
        raw_array = cv2.imread(str(filepath), cv2.IMREAD_UNCHANGED)
        assert raw_array is not None
        raw_array[..., :3] = raw_array[..., 2::-1]

        # Correct the gamma of the raw array
        gamma = 2.2
        array_gamma = np.power(np.clip(raw_array, 0, 1), 1 / gamma)
        array = (array_gamma * 255).astype(np.uint8)

        im = Image.fromarray(array, mode="RGBA")

        # Paste solid background
        if im.mode == "RGBA":
            new_bg = Image.new("RGB", im.size, color="#1e1e1e")
            new_bg.paste(im, mask=im.getchannel(3))
            im = new_bg

    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im


def raw_image_thumb(filepath: Path) -> Image.Image | None:
    """Render a thumbnail for a RAW image type.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image.Image | None = None
    try:
        with rawpy.imread(str(filepath)) as raw:
            rgb = raw.postprocess(use_camera_wb=True)
            im = Image.frombytes(
                "RGB",
                (rgb.shape[1], rgb.shape[0]),
                rgb,
                decoder_name="raw",
            )
    except (
        DecompressionBombError,
        LibRawIOError,
        LibRawFileUnsupportedError,
    ) as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im


def image_from_bytes(image_data: BytesIO) -> Image.Image:
    """Load a raster image and add a background if it's transparent.

    Args:
        image_data (BytesIO): The binary image data.

    Returns:
        Image.Image: The loaded raster image, with a background if needed.
    """
    im: Image.Image = Image.open(image_data)
    if im.mode != "RGB" and im.mode != "RGBA":
        im = im.convert(mode="RGBA")
    if im.mode == "RGBA":
        new_bg = Image.new("RGB", im.size, color="#1e1e1e")
        new_bg.paste(im, mask=im.getchannel(3))
        im = new_bg
    return unwrap(ImageOps.exif_transpose(im))
