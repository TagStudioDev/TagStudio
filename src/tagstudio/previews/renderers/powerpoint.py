# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.renderers.archive import archive_thumb

logger = structlog.get_logger(__name__)

MediaTypes.register("microsoft.office.powerpoint", ".pptx", RENDER)


class PowerPointPreview(BasePreview):
    _fallback_icon = "presentation"
    media_type_name = "microsoft.office.powerpoint"

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
        return powerpoint_thumb(filepath)


def powerpoint_thumb(filepath: Path) -> Image | None:
    """Extract and render a thumbnail for a Microsoft PowerPoint file."""
    image_names = ["docProps/thumbnail.jpeg"]
    return archive_thumb(filepath, image_names)
