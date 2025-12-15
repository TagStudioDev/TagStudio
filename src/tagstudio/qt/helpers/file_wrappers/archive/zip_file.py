import zipfile
from pathlib import Path
from types import TracebackType
from typing import Literal, Self

from tagstudio.qt.helpers.file_wrappers.archive.archive_file import ArchiveFile


class ZipFile(ArchiveFile):
    """Wrapper around zipfile.ZipFile."""

    def __init__(self, path: Path, mode: Literal["r"]) -> None:
        super().__init__(path, mode)
        self.path = path
        self.__zip_file: zipfile.ZipFile = zipfile.ZipFile(path, mode)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        self.__zip_file.close()

    def get_name_list(self) -> list[str]:
        without_own_file_name: map = map(
            lambda file_name: file_name.replace(f"{self.path.name}/", ""),
            self.__zip_file.namelist(),
        )
        without_empty_items: filter = filter(None, without_own_file_name)

        return list(without_empty_items)

    def has_file_name(self, file_name: str) -> bool:
        return file_name in self.get_name_list()

    def read(self, file_name: str) -> bytes | None:
        search_paths: list[Path] = [Path(file_name), Path(self.path.name, file_name)]
        try:
            for file_path in search_paths:
                try:
                    return self.__zip_file.read(str(file_path))
                except KeyError:
                    continue

            return None
        except KeyError as e:
            raise e
