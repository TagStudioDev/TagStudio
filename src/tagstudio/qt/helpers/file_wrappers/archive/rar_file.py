from pathlib import Path
from typing import Literal

import rarfile

from tagstudio.qt.helpers.file_wrappers.archive.archive_file import ArchiveFile


class RarFile(ArchiveFile):
    """Wrapper around rarfile.RarFile."""

    def __init__(self, path: Path, mode: Literal["r"]) -> None:
        super().__init__(path, mode)
        self.__rar_file: rarfile.RarFile = rarfile.RarFile(path, mode)

    def get_name_list(self) -> list[str]:
        return self.__rar_file.namelist()

    def has_file_name(self, file_name: str) -> bool:
        return file_name in self.get_name_list()

    def read(self, file_name: str) -> bytes:
        return self.__rar_file.read(file_name)
