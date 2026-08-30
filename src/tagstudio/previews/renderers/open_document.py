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

MediaTypes.register("open_document", ".fodg", RENDER)
MediaTypes.register("open_document", ".fodp", RENDER)
MediaTypes.register("open_document", ".fods", RENDER)
MediaTypes.register("open_document", ".fodt", RENDER)
MediaTypes.register("open_document", ".mscz", RENDER)
MediaTypes.register("open_document", ".odf", RENDER)
MediaTypes.register("open_document", ".odg", RENDER)
MediaTypes.register("open_document", ".odp", RENDER)
MediaTypes.register("open_document", ".ods", RENDER)
MediaTypes.register("open_document", ".odt", RENDER)
MediaTypes.register("open_document", ".ora", RENDER)


class OpenDocumentPreview(BasePreview):
    media_type_name = "open_document"

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
        return open_doc_thumb(filepath)


def open_doc_thumb(filepath: Path) -> Image | None:
    """Extract and render a thumbnail for an OpenDocument file."""
    image_names = ["Thumbnails/thumbnail.png"]
    return archive_thumb(filepath, image_names)
