# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

# pyright: standard


from pathlib import Path

from PIL.Image import Image

from tagstudio.core.enums import Theme

RENDER = "RENDER"


class BasePreview:
    """A base preview renderer class.

    Attributes:
        media_type_name (str):  Used for identifying the MediaType.
        priority (int): Render priority over other Preview classes.
    """

    media_type_name: str
    priority: int = 50

    def __init__(self) -> None:
        pass

    @classmethod
    def render(
        cls,
        filepath: Path,
        is_small: bool,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image | None:
        raise NotImplementedError
