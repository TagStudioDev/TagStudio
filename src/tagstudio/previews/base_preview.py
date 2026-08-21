# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

# pyright: standard


from pathlib import Path

from PIL.Image import Image

from tagstudio.core.enums import Theme


class BasePreview:
    """A base preview renderer class."""

    # The attribute name used for identifying the MediaType used with the preview renderer.
    media_type_name: str

    def __init__(self) -> None:
        pass

    @classmethod
    def render(
        cls,
        filepath: Path,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image | None:
        raise NotImplementedError
