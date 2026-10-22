# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.vendored.blender_thumbnailer import blend_thumb

logger = structlog.get_logger(__name__)


class BlenderPreview(BasePreview):
    media_type_name = "blender"
    priority = 40

    @override
    @classmethod
    def register_types(cls) -> None:
        # NOTE: Filetype equivalents (i.e. ".blend1" == ".blend32") are already declared internally.
        MediaTypes.register("blender", ".blend", RENDER)
        MediaTypes.register("blender", ".blend1", RENDER)

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
        return _blender_thumb(filepath)


def _blender_thumb(filepath: Path) -> Image | None:
    """Get an emended thumbnail from a Blender file, if a thumbnail is present.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image | None = None
    try:
        im = blend_thumb(str(filepath))
        if im is None:
            logger.info(
                f"[ThumbRenderer][BLENDER][INFO] {filepath.name} "
                "Doesn't have an embedded thumbnail."
            )
    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im
