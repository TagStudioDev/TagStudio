import tarfile
from pathlib import Path
from typing import Literal

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.helpers.file_wrappers.archive.archive_file import ArchiveFile


class TarFile(ArchiveFile):
    """Wrapper around tarfile.TarFile."""

    def __init__(self, path: Path, mode: Literal["r"]) -> None:
        super().__init__(path, mode)
        self.__tar_file: tarfile.TarFile = tarfile.TarFile(path, mode)

    def get_name_list(self) -> list[str]:
        return self.__tar_file.getnames()

    def has_file_name(self, file_name: str) -> bool:
        return file_name in self.get_name_list()

    def read(self, file_name: str) -> bytes:
        return unwrap(self.__tar_file.extractfile(file_name)).read()
