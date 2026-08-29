# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import override

import rawpy
import structlog
from PIL.Image import DecompressionBombError, Image, frombytes
from rawpy import (
    LibRawFileUnsupportedError,  # pyright: ignore[reportPrivateImportUsage]
    LibRawIOError,  # pyright: ignore[reportPrivateImportUsage]
)

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview

logger = structlog.get_logger(__name__)

MediaTypes.register("image.raw", ".arw", RENDER)
MediaTypes.register("image.raw", ".cr2", RENDER)
MediaTypes.register("image.raw", ".cr3", RENDER)
MediaTypes.register("image.raw", ".crw", RENDER)
MediaTypes.register("image.raw", ".dng", RENDER)
MediaTypes.register("image.raw", ".nef", RENDER)
MediaTypes.register("image.raw", ".nrw", RENDER)
MediaTypes.register("image.raw", ".orf", RENDER)
MediaTypes.register("image.raw", ".r3d", RENDER)
MediaTypes.register("image.raw", ".raf", RENDER)
MediaTypes.register("image.raw", ".raw", RENDER)
MediaTypes.register("image.raw", ".rw2", RENDER)
MediaTypes.register("image.raw", ".srf", RENDER)
MediaTypes.register("image.raw", ".srf2", RENDER)


class RawImagePreview(BasePreview):
    media_type_name = "image.raw"
    priority = 60

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
        return raw_image_thumb(filepath)


def raw_image_thumb(filepath: Path) -> Image | None:
    """Render a thumbnail for a RAW image type.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image | None = None
    try:
        with rawpy.imread(str(filepath)) as raw:
            rgb = raw.postprocess(use_camera_wb=True)
            im = frombytes(
                "RGB",
                (rgb.shape[1], rgb.shape[0]),
                rgb,
                decoder_name="raw",
            )
    except (
        DecompressionBombError,
        LibRawFileUnsupportedError,
        LibRawIOError,
    ) as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im
