# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import sqlite3
from io import BytesIO
from pathlib import Path

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


def clip_studio_thumb(filepath: Path) -> Image.Image | None:
    """Extract the thumbnail from the SQLite database embedded in a .clip file.

    Args:
        filepath (Path): The path of the .clip file.

    Returns:
        Image: The embedded thumbnail, if extractable.
    """
    im: Image.Image | None = None
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
                im = Image.open(BytesIO(thumbnail[0]))
        conn.close()
    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

    return im
