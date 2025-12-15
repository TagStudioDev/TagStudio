from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(kw_only=True)
class RendererContext:
    path: Path
    extension: str
    size: int
    pixel_ratio: float
    is_grid_thumb: bool


class BaseRenderer(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @staticmethod
    @abstractmethod
    def render(context: RendererContext) -> Image.Image | None:
        raise NotImplementedError
