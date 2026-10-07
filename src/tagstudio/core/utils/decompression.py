# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from collections.abc import Callable, Generator
from compression import bz2, gzip, lzma, zstd
from contextlib import contextmanager
from io import BufferedIOBase
from pathlib import Path
from tempfile import TemporaryDirectory

import structlog

from tagstudio.core.media_types import MediaTypes
from tagstudio.core.query_lang.file_groups import SEARCH

logger = structlog.get_logger(__name__)

MAX_DECOMPRESSED_SIZE: int = 128 * 1024 * 1024  # 128 MiB
_CHUNK_SIZE: int = 1024 * 1024

_OPENERS: dict[str, Callable[[Path], BufferedIOBase]] = {
    ".bz": lambda path: bz2.open(path, "rb"),
    ".bz2": lambda path: bz2.open(path, "rb"),
    ".gz": lambda path: gzip.open(path, "rb"),
    ".lzma": lambda path: lzma.open(path, "rb"),
    ".xz": lambda path: lzma.open(path, "rb"),
    ".zst": lambda path: zstd.open(path, "rb"),
}


def is_compressed(path: Path) -> bool:
    """Return `True` if the file is a compressed file."""
    return MediaTypes.contains("compressed", path.suffix.lower(), SEARCH)


def get_inner_ext(path: Path) -> str | None:
    """Return the extension of the file inside a compressed file, if it's a known file type."""
    if not is_compressed(path) or MediaTypes.get_ext(path) != path.suffix.lower():
        return None
    inner_ext = MediaTypes.get_ext(Path(path.stem))
    return inner_ext if MediaTypes.find(inner_ext, SEARCH) else None


def get_display_ext(path: Path) -> str:
    """Return a file's extension, including the inner file type if compressed (e.g. ".png.gz")."""
    inner_ext = get_inner_ext(path)
    return f"{inner_ext}{path.suffix.lower()}" if inner_ext else MediaTypes.get_ext(path)


def decompress(path: Path, dest: Path, max_size: int = MAX_DECOMPRESSED_SIZE) -> bool:
    """Decompress a file to dest, stopping and returning `False` if it exceeds max_size bytes."""
    size = 0
    with _OPENERS[path.suffix.lower()](path) as source, open(dest, "wb") as out:
        while chunk := source.read(_CHUNK_SIZE):
            size += len(chunk)
            if size > max_size:
                return False
            out.write(chunk)
    return True


@contextmanager
def decompressed(path: Path, max_size: int = MAX_DECOMPRESSED_SIZE) -> Generator[Path | None]:
    """Yield a path to a file's uncompressed contents, or `None` if it can't be decompressed."""
    if not is_compressed(path):
        yield path
        return

    if path.suffix.lower() not in _OPENERS:
        logger.info("[Decompression] Unsupported compression format", path=path)
        yield None
        return

    # NOTE: Windows can't delete a file that a reader still has open, so cleanup can't be strict.
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir) / path.stem
        try:
            is_decompressed = decompress(path, temp_path, max_size)
        except (EOFError, OSError, lzma.LZMAError, zstd.ZstdError) as e:
            logger.error("[Decompression] Could not decompress file", path=path, error=e)
            is_decompressed = False
        else:
            if not is_decompressed:
                logger.warning("[Decompression] File is too large to decompress", path=path)

        yield temp_path if is_decompressed else None
