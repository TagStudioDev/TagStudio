# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

import structlog
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from tagstudio.previews.vendored.blender_thumbnailer import blend_thumb

logger = structlog.get_logger(__name__)


def blender_thumb(filepath: Path) -> Image.Image | None:
    """Get an emended thumbnail from a Blender file, if a thumbnail is present.

    Args:
        filepath (Path): The path of the file.
    """
    bg_color: str = (
        "#1e1e1e"
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else "#FFFFFF"
    )
    im: Image.Image | None = None
    try:
        if (blend_image := blend_thumb(str(filepath))) is not None:
            bg = Image.new("RGB", blend_image.size, color=bg_color)
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
