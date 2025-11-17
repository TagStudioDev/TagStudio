from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image


class BaseRenderer(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @staticmethod
    @abstractmethod
    def render(path: Path) -> Image.Image | None:
        raise NotImplementedError
