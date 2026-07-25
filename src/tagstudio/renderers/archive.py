# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import tarfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Literal

import py7zr
import py7zr.io
import rarfile
import structlog
from PIL import Image

from tagstudio.core.media_types import MediaCategories
from tagstudio.core.utils.types import unwrap
from tagstudio.renderers.raster_image import load_raster_image

logger = structlog.get_logger(__name__)

type Archive = zipfile.ZipFile | rarfile.RarFile | SevenZipFile | TarFile


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

    def __enter__(self) -> "TarFile":
        self.tar = tarfile.open(name=self.filepath, mode=self.mode).__enter__()
        return self

    def __exit__(self, *args) -> None:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        self.tar.__exit__(*args)


def archive_thumb(filepath: Path, ext: str) -> Image.Image | None:
    """Extract the first image found in the archive.

    Args:
        filepath (Path): The path to the archive.
        ext (str): The file extension.

    Returns:
        Image: The first image found in the archive.
    """
    im: Image.Image | None = None
    try:
        with open_archive(filepath, ext) as archive:
            im = first_image(archive)
    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

    return im


def open_archive(filepath: Path, ext: str) -> Archive:
    """Open an archive with its corresponding archiver.

    Args:
        filepath (Path): The path to the archive.
        ext (str): The file extension.

    Returns:
        Archive: The opened archive.
    """
    archiver: type[Archive] = zipfile.ZipFile
    if ext in {".7z", ".cb7", ".s7z"}:
        archiver = SevenZipFile
    elif ext in {".cbr", ".rar"}:
        archiver = rarfile.RarFile
    elif ext in {".cbt", ".tar", ".tgz"}:
        archiver = TarFile
    return archiver(filepath, "r")


def first_image(archive: Archive) -> Image.Image | None:
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
            return load_raster_image(BytesIO(image_data))

    return None
