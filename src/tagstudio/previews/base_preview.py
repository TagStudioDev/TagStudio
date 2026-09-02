# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

# pyright: standard


from pathlib import Path

from PIL.Image import Image

from tagstudio.core.enums import Theme

RENDER = "RENDER"  # MediaType Context


class BasePreview:
    """A base preview renderer class.

    Attributes:
        _fallback_icon (str): The name of the fallback icon resource to use, if needed.
        media_type_name (str):  Used for identifying the MediaType.
        priority (int): Render priority over other Preview classes.
    """

    _fallback_icon: str = ""
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

    @classmethod
    def icon_name(cls) -> str:
        """Get the name of the fallback icon resource associated with this renderer."""
        return cls._fallback_icon or cls.media_type_name
