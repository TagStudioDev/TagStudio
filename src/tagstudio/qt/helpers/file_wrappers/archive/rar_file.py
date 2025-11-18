from pathlib import Path
from types import TracebackType
from typing import Literal, Self

import rarfile

from tagstudio.qt.helpers.file_wrappers.archive.archive_file import ArchiveFile


class RarFile(ArchiveFile):
    """Wrapper around rarfile.RarFile."""

    def __init__(self, path: Path, mode: Literal["r"]) -> None:
        super().__init__(path, mode)
        self.__rar_file: rarfile.RarFile = rarfile.RarFile(path, mode)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        self.__rar_file.close()

    def get_name_list(self) -> list[str]:
        return self.__rar_file.namelist()

    def has_file_name(self, file_name: str) -> bool:
        return file_name in self.get_name_list()

    def read(self, file_name: str) -> bytes:
        return self.__rar_file.read(file_name)
