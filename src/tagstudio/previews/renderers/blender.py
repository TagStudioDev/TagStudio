# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image
from PIL.Image import new as new_image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.vendored.blender_thumbnailer import blend_thumb

logger = structlog.get_logger(__name__)

# NOTE: Filetype equivalents (i.e. ".blend1" == ".blend32") are already declared internally.
MediaTypes.register("blender", ".blend", RENDER)
MediaTypes.register("blender", ".blend1", RENDER)


class BlenderPreview(BasePreview):
    media_type_name = "blender"
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
        return _blender_thumb(filepath, theme)


def _blender_thumb(filepath: Path, theme: Theme) -> Image | None:
    """Get an emended thumbnail from a Blender file, if a thumbnail is present.

    Args:
        filepath (Path): The path of the file.
        theme (Theme): The system color theme.
    """
    bg_color: str = "#1e1e1e" if theme == Theme.DARK else "#FFFFFF"
    im: Image | None = None
    try:
        if (blend_image := blend_thumb(str(filepath))) is not None:
            bg = new_image("RGB", blend_image.size, color=bg_color)
            bg.paste(blend_image, mask=blend_image.getchannel(3))
            im = bg
        else:
            logger.info(
                f"[ThumbRenderer][BLENDER][INFO] {filepath.name} "
                "Doesn't have an embedded thumbnail."
            )
    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im
