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
from tagstudio.previews.renderers.raster_image import image_from_bytes

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

    def __enter__(self) -> TarFile:
        self.tar = tarfile.open(name=self.filepath, mode=self.mode).__enter__()
        return self

    def __exit__(self, *args) -> None:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        self.tar.__exit__(*args)


def open_archive(filepath: Path, ext: str = "") -> Archive:
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


def first_image_in_archive(archive: Archive) -> Image.Image | None:
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
    ext: str = "",
) -> Image.Image | None:
    """Extract an embedded preview image from an archive.

    Args:
        filepath (Path): The path to the archive.
        image_names: (list[Path] | list[str] | None): List of embedded image names to search for.
        ext (str): The file extension. Used to help determine more specific archive type.

    Returns:
        Image: The first image found in the archive.
    """
    try:
        with open_archive(filepath, ext) as archive:
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


def apple_embedded_thumb(filepath: Path) -> Image.Image | None:
    """Extract and render an apple embedded thumbnail (iWork, Apple Creative Studio)."""
    image_names: list[str] = [
        "preview.jpg",
        "QuickLook/Preview.heic",
        "QuickLook/Thumbnail.jpg",
        "QuickLook/Thumbnail.heic",
        "QuickLook/Thumbnail.webp",
        "QuickLook/Icon.webp",
    ]
    return archive_thumb(filepath, image_names)


def krita_thumb(filepath: Path) -> Image.Image | None:
    """Extract and render a thumbnail for a Krita file."""
    image_names = ["preview.png"]
    return archive_thumb(filepath, image_names)


def open_doc_thumb(filepath: Path) -> Image.Image | None:
    """Extract and render a thumbnail for an OpenDocument file."""
    image_names = ["Thumbnails/thumbnail.png"]
    return archive_thumb(filepath, image_names)


def powerpoint_thumb(filepath: Path) -> Image.Image | None:
    """Extract and render a thumbnail for a Microsoft PowerPoint file."""
    image_names = ["docProps/thumbnail.jpeg"]
    return archive_thumb(filepath, image_names)
