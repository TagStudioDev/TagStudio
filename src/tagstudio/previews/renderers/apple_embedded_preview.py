# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image

from tagstudio.core.enums import Theme
from tagstudio.previews.base_preview import BasePreview
from tagstudio.previews.renderers.archive import archive_thumb

logger = structlog.get_logger(__name__)


class AppleEmbeddedPreview(BasePreview):
    media_type_name = "iwork"

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
        return apple_embedded_thumb(filepath)


def apple_embedded_thumb(filepath: Path) -> Image | None:
    """Extract and render an apple embedded thumbnail (iWork, Apple Creative Studio)."""
    image_names: list[str] = [
        "preview.jpg",
        "QuickLook/Preview.heic",
        "QuickLook/Thumbnail.jpg",
        "QuickLook/Thumbnail.heic",
        "QuickLook/Thumbnail.webp",
        "QuickLook/Icon.webp",
    ]
    return archive_thumb(filepath, image_names)
