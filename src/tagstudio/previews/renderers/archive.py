# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from io import BytesIO
from pathlib import Path
from tarfile import TarFile
from typing import Self, override
from zipfile import ZipFile

import structlog
from PIL.Image import Image
from py7zr import SevenZipFile
from py7zr.io import BytesIOFactory
from rarfile import RarFile

from tagstudio.core.enums import Theme
from tagstudio.core.media_types import MediaTypes
from tagstudio.core.utils.types import unwrap
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.renderers.raster_image import image_from_bytes

logger = structlog.get_logger(__name__)

type Archive = Rar | SevenZip | Tar | Zip


class ArchivePreview(BasePreview):
    media_type_name = "archive"

    @override
    @classmethod
    def register_types(cls) -> None:
        # NOTE: Filetype equivalents (i.e. ".tar.gz" == ".tgz") are already declared internally.
        MediaTypes.register("archive", [".7z", ".s7z"], RENDER)
        MediaTypes.register("archive", ".gz", RENDER)
        MediaTypes.register("archive", ".rar", RENDER)
        MediaTypes.register("archive", ".tar", RENDER)
        MediaTypes.register("archive", ".zip", RENDER)
        MediaTypes.register("archive", [".bz", ".bz2"], RENDER)
        MediaTypes.register("archive", ".xz", RENDER)
        MediaTypes.register("archive", [".taz", ".tgz"], RENDER)
        MediaTypes.register("archive", [".tb2", ".tbz", ".tbz2", ".tz2"], RENDER)
        MediaTypes.register("archive", ".tlz", RENDER)
        MediaTypes.register("archive", ".txz", RENDER)
        MediaTypes.register("archive", ".zst", RENDER)
        MediaTypes.register("archive", ".lzma", RENDER)
        MediaTypes.register("archive", ".tzst", RENDER)

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


class Rar(RarFile):
    """Wrapper around RarFile for a unified API."""

    @classmethod
    def open_archive(cls, filepath: Path) -> Self:
        return cls(filepath, "r")


class SevenZip(SevenZipFile):
    """Wrapper around SevenZipFile for a unified API."""

    @classmethod
    def open_archive(cls, filepath: Path) -> Self:
        return cls(filepath, "r")

    def read(self, name: str) -> bytes:
        # SevenZipFile must be reset after every extraction
        # See https://py7zr.readthedocs.io/en/stable/api.html#py7zr.SevenZipFile.extract
        self.reset()
        factory = BytesIOFactory(limit=10485760)  # 10 MiB
        self.extract(targets=[name], factory=factory)
        return factory.get(name).read()


class Tar(TarFile):
    """Wrapper around TarFile for a unified API."""

    @classmethod
    def open_archive(cls, filepath: Path) -> Self:
        return cls.open(filepath, "r")

    def namelist(self) -> list[str]:
        return self.getnames()

    def read(self, name: str) -> bytes:
        return unwrap(self.extractfile(name)).read()


class Zip(ZipFile):
    """Wrapper around ZipFile for a unified API."""

    @classmethod
    def open_archive(cls, filepath: Path) -> Self:
        return cls(filepath, "r")


def open_archive(filepath: Path) -> Archive:
    """Open an archive with its corresponding archiver.

    Args:
        filepath (Path): The path to the archive.

    Returns:
        Archive: The opened archive.
    """
    ext = filepath.suffix.lower()
    archiver: type[Archive] = Zip
    if ext in {".7z", ".cb7", ".s7z"}:
        archiver = SevenZip
    elif ext in {".cbr", ".rar"}:
        archiver = Rar
    elif ext in {
        ".cbt",
        ".taz",
        ".tb2",
        ".tbz",
        ".tbz2",
        ".tgz",
        ".tlz",
        ".txz",
        ".tz2",
        ".tzst",
    } or ".tar" in [suffix.lower() for suffix in filepath.suffixes]:
        archiver = Tar
    return archiver.open_archive(filepath)


def first_image_in_archive(archive: Archive) -> Image | None:
    """Find and extract the first renderable image in the archive.

    Args:
        archive (Archive): The current archive.

    Returns:
        Image: The first renderable image in the archive.
    """
    for file_name in archive.namelist():  # pyright: ignore[reportUnknownVariableType]
        ext = Path(file_name).suffix
        if MediaTypes.image_raster.contains(ext, RENDER):
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
