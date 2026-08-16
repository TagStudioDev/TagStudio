# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

import srctools
import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


def vtf_thumb(filepath: Path) -> Image.Image | None:
    """Extract and render a thumbnail for VTF (Valve Texture Format) images.

    Uses the srctools library for reading VTF files.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image.Image | None = None
    try:
        with open(filepath, "rb") as f:
            vtf = srctools.VTF.read(f)
            im = vtf.get(frame=0).to_PIL()

    except (ValueError, FileNotFoundError) as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im
