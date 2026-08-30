# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import sqlite3
from io import BytesIO
from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image
from PIL.Image import open as open_image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview

logger = structlog.get_logger(__name__)

MediaTypes.register("clip_studio_paint", ".clip", RENDER)


class ClipStudioPaintPreview(BasePreview):
    media_type_name = "clip_studio_paint"

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
        return clip_studio_thumb(filepath)


def clip_studio_thumb(filepath: Path) -> Image | None:
    """Extract the thumbnail from the SQLite database embedded in a .clip file.

    Args:
        filepath (Path): The path of the .clip file.

    Returns:
        Image: The embedded thumbnail, if extractable.
    """
    im: Image | None = None
    try:
        with open(filepath, "rb") as f:
            blob = f.read()
            sqlite_index = blob.find(b"SQLite format 3")
            if sqlite_index == -1:
                return im

        with sqlite3.connect(":memory:") as conn:
            conn.deserialize(blob[sqlite_index:])
            thumbnail = conn.execute("SELECT ImageData FROM CanvasPreview").fetchone()
            if thumbnail:
                im = open_image(BytesIO(thumbnail[0]))
        conn.close()
    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

    return im
