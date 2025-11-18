from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image


class BaseRenderer(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @staticmethod
    @abstractmethod
    def render(path: Path, extension: str, size: int, is_grid_thumb: bool) -> Image.Image | None:
        raise NotImplementedError
