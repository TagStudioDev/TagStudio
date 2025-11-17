from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal


class ArchiveFile(ABC):
    @abstractmethod
    def __init__(self, path: Path, mode: Literal["r"]) -> None:
        pass

    @abstractmethod
    def get_name_list(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def has_file_name(self, file_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def read(self, file_name: str) -> bytes:
        raise NotImplementedError
