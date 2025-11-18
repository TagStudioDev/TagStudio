from pathlib import Path
from types import TracebackType
from typing import Literal, Self

import py7zr

from tagstudio.qt.helpers.file_wrappers.archive.archive_file import ArchiveFile


class SevenZipFile(ArchiveFile):
    """Wrapper around py7zr.SevenZipFile."""

    def __init__(self, path: Path, mode: Literal["r"]) -> None:
        super().__init__(path, mode)
        self.__seven_zip_file: py7zr.SevenZipFile = py7zr.SevenZipFile(path, mode)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        self.__seven_zip_file.close()

    def get_name_list(self) -> list[str]:
        return self.__seven_zip_file.namelist()

    def has_file_name(self, file_name: str) -> bool:
        return file_name in self.get_name_list()

    def read(self, file_name: str) -> bytes:
        # py7zr.SevenZipFile must be reset after every extraction
        # See https://py7zr.readthedocs.io/en/stable/api.html#py7zr.SevenZipFile.extract
        self.__seven_zip_file.reset()

        factory = py7zr.io.BytesIOFactory(limit=10485760)  # 10 MiB
        self.__seven_zip_file.extract(targets=[file_name], factory=factory)
        return factory.get(file_name).read()
