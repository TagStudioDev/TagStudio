# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaType, MediaTypeGroup, MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.renderers.archive import archive_thumb

logger = structlog.get_logger(__name__)

MediaTypes.register_group(
    MediaTypeGroup(
        "iwork",
        [
            MediaType(".key", RENDER),
            MediaType(".numbers", RENDER),
            MediaType(".pages", RENDER),
            MediaType(".pxd", RENDER),
        ],
    )
)


class AppleEmbeddedPreview(BasePreview):
    media_type_name = "iwork"

    image_names: list[str] = [
        "preview.jpg",
        "QuickLook/Preview.heic",
        "QuickLook/Thumbnail.jpg",
        "QuickLook/Thumbnail.heic",
        "QuickLook/Thumbnail.webp",
        "QuickLook/Icon.webp",
    ]

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
        return cls.apple_embedded_thumb(filepath)

    @classmethod
    def apple_embedded_thumb(cls, filepath: Path) -> Image | None:
        """Extract and render an apple embedded thumbnail (iWork, Apple Creative Studio)."""
        return archive_thumb(filepath, cls.image_names)
