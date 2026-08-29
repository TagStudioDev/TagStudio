# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

# TODO: Remove this file from the project, turning it into an external plugin.

from pathlib import Path
from typing import override

import srctools
import structlog
from PIL.Image import Image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import SEARCH, MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview

logger = structlog.get_logger(__name__)

# By individual type
MediaTypes.register("code", ".fgd", [SEARCH, RENDER])
MediaTypes.register("code", ".gi", [SEARCH, RENDER])
MediaTypes.register("code", ".kv3", [SEARCH, RENDER])
MediaTypes.register("code", ".nut", [SEARCH, RENDER])
MediaTypes.register("code", ".vcfg", [SEARCH, RENDER])
MediaTypes.register("code", ".vdf", [SEARCH, RENDER])
MediaTypes.register("code", ".vqlayout", [SEARCH, RENDER])
MediaTypes.register("code", ".vsc", [SEARCH, RENDER])
MediaTypes.register("code", ".vsnd_template", [SEARCH, RENDER])
MediaTypes.register("source_engine", ".vtf", [SEARCH, RENDER])
MediaTypes.register("source_engine", ".vmt", SEARCH)


class SourceEnginePreview(BasePreview):
    media_type_name = "source_engine"

    @classmethod
    @override
    def render(
        cls,
        filepath: Path,
        is_small: bool,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image | None:
        return vtf_thumb(filepath)


def vtf_thumb(filepath: Path) -> Image | None:
    """Extract and render a thumbnail for VTF (Valve Texture Format) images.

    Uses the srctools library for reading VTF files.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image | None = None
    try:
        with open(filepath, "rb") as f:
            vtf = srctools.VTF.read(f)
            im = vtf.get(frame=0).to_PIL()

    except (ValueError, FileNotFoundError) as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im
