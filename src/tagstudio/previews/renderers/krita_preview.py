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


class KritaPreview(BasePreview):
    media_type_name = "krita"

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
        return krita_thumb(filepath)


def krita_thumb(filepath: Path) -> Image | None:
    """Extract and render a thumbnail for a Krita file."""
    image_names = ["preview.png"]
    return archive_thumb(filepath, image_names)
