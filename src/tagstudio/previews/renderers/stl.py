# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.stl_renderer import StlRenderError, render_stl_thumbnail

logger = structlog.get_logger(__name__)

# TODO: Make these parameters configurable
_MAX_STL_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
_MAX_STL_TRIANGLES = 250_000


class STLPreview(BasePreview):
    media_type_name = "model.stl"
    _fallback_icon = "model"

    @override
    @classmethod
    def register_types(cls) -> None:
        MediaTypes.register("model.stl", ".stl", RENDER)

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
        return _stl_thumb(filepath, theme, size)


def _stl_thumb(filepath: Path, theme: Theme, size: tuple[int, int]) -> Image | None:
    """Render a thumbnail for an STL file.

    Args:
        filepath (Path): The path of the file.
        theme (Theme): The system color theme.
        size (tuple[int, int]): The target size of the thumbnail.
    """
    bg_color: str = "#1e1e1e" if theme == Theme.DARK else "#FFFFFF"
    im: Image | None = None
    try:
        im = render_stl_thumbnail(
            filepath=filepath,
            size=max(size),
            bg_color=bg_color,
            max_file_size=_MAX_STL_FILE_SIZE,
            max_triangles=_MAX_STL_TRIANGLES,
        )
    except StlRenderError as e:
        logger.info("Skipping STL thumbnail", filename=filepath.name, error=str(e))
    except Exception as e:
        logger.error("Couldn't render thumbnail", filename=filepath.name, error=type(e).__name__)
    return im
