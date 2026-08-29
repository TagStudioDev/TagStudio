# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import tarfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Literal, override

import py7zr
import py7zr.io
import rarfile
import structlog
from PIL.Image import Image

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaCategories, MediaTypes
from tagstudio.core.utils.types import unwrap
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.renderers.raster_image import image_from_bytes

logger = structlog.get_logger(__name__)

type Archive = zipfile.ZipFile | rarfile.RarFile | SevenZipFile | TarFile

# NOTE: Filetype equivalents (i.e. ".tar.gz" == ".tgz") are already declared internally.
MediaTypes.register("archive", ".7z", RENDER)
MediaTypes.register("archive", ".gz", RENDER)
MediaTypes.register("archive", ".rar", RENDER)
MediaTypes.register("archive", ".s7z", RENDER)
MediaTypes.register("archive", ".tar", RENDER)
MediaTypes.register("archive", ".zip", RENDER)
MediaTypes.register("archive", ".tar.gz", RENDER)


class ArchivePreview(BasePreview):
    media_type_name = "archive"

    @override
    @classmethod
    def render(
        cls,
        filepath: Path,
        is_small: bool,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image | None:
        return archive_thumb(filepath)


class SevenZipFile(py7zr.SevenZipFile):
    """Wrapper around py7zr.SevenZipFile to mimic zipfile.ZipFile's API."""

    def __init__(self, filepath: Path, mode: Literal["r"]) -> None:
        super().__init__(filepath, mode)

    def read(self, name: str) -> bytes:
        # SevenZipFile must be reset after every extraction
        # See https://py7zr.readthedocs.io/en/stable/api.html#py7zr.SevenZipFile.extract
        self.reset()
        factory = py7zr.io.BytesIOFactory(limit=10485760)  # 10 MiB
        self.extract(targets=[name], factory=factory)
        return factory.get(name).read()


class TarFile:
    """Wrapper around tarfile.TarFile to mimic zipfile.ZipFile's API."""

    def __init__(self, filepath: Path, mode: Literal["r"]) -> None:
        self.tar: tarfile.TarFile
        self.filepath = filepath
        self.mode: Literal["r"] = mode

    def namelist(self) -> list[str]:
        return self.tar.getnames()

    def read(self, name: str) -> bytes:
        return unwrap(self.tar.extractfile(name)).read()

    def __enter__(self) -> TarFile:
        self.tar = tarfile.open(name=self.filepath, mode=self.mode).__enter__()
        return self

    def __exit__(self, *args) -> None:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        self.tar.__exit__(*args)


def open_archive(filepath: Path) -> Archive:
    """Open an archive with its corresponding archiver.

    Args:
        filepath (Path): The path to the archive.
        ext (str): The file extension.

    Returns:
        Archive: The opened archive.
    """
    ext = filepath.suffix.lower()
    archiver: type[Archive] = zipfile.ZipFile
    if ext in {".7z", ".cb7", ".s7z"}:
        archiver = SevenZipFile
    elif ext in {".cbr", ".rar"}:
        archiver = rarfile.RarFile
    elif ext in {".cbt", ".tar", ".tgz"}:
        archiver = TarFile
    return archiver(filepath, "r")


def first_image_in_archive(archive: Archive) -> Image | None:
    """Find and extract the first renderable image in the archive.

    Args:
        archive (Archive): The current archive.

    Returns:
        Image: The first renderable image in the archive.
    """
    for file_name in archive.namelist():  # pyright: ignore[reportUnknownVariableType]
        ext = Path(file_name).suffix
        if MediaCategories.IMAGE_RASTER_TYPES.contains(ext):
            image_data = archive.read(file_name)  # pyright: ignore[reportUnknownVariableType]
            return image_from_bytes(BytesIO(image_data))

    return None


def archive_thumb(
    filepath: Path,
    image_names: list[Path] | list[str] | None = None,
) -> Image | None:
    """Extract an embedded preview image from an archive.

    Args:
        filepath (Path): The path to the archive.
        image_names: (list[Path] | list[str] | None): List of embedded image names to search for.
        ext (str): The file extension. Used to help determine more specific archive type.

    Returns:
        Image: The first image found in the archive.
    """
    try:
        with open_archive(filepath) as archive:
            # If no list of image names to search for was provided, default to the first image.
            if not image_names:
                return first_image_in_archive(archive)

            for image_name in image_names:
                if image_name in archive.namelist():
                    file_data = archive.read(str(image_name))  # pyright: ignore[reportUnknownVariableType]
                    return image_from_bytes(BytesIO(file_data))

            # If no images were found with the given names, fallback to the first image found.
            if not image_names:
                return first_image_in_archive(archive)

    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return None
