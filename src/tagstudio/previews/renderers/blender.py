# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image, new

from tagstudio.core.enums import Theme
from tagstudio.previews.base_preview import BasePreview
from tagstudio.previews.vendored.blender_thumbnailer import blend_thumb

logger = structlog.get_logger(__name__)


class BlenderPreview(BasePreview):
    media_type_name = "blender"

    @override
    @classmethod
    def render(
        cls,
        filepath: Path,
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
            bg = new("RGB", blend_image.size, color=bg_color)
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
