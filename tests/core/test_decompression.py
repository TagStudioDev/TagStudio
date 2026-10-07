# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

# pyright: reportPrivateUsage=false


from compression import gzip
from pathlib import Path

import pytest

from tagstudio.core.media_types import MediaTypes
from tagstudio.core.query_lang.file_groups import SEARCH
from tagstudio.core.utils.decompression import (
    decompress,
    decompressed,
    get_display_ext,
    get_inner_ext,
    is_compressed,
)


@pytest.mark.parametrize(
    ["filename", "expected"],
    [("photo.png.gz", True), ("Photo.PNG.XZ", True), ("photo.png", False), ("bundle.zip", False)],
)
def test_is_compressed(filename: str, expected: bool):
    assert is_compressed(Path(filename)) is expected


def test_unsupported_compression_format(tmp_path: Path):
    MediaTypes.register("compressed", ".zzzcomp", SEARCH)
    source = tmp_path / "photo.png.zzzcomp"
    source.touch()

    assert is_compressed(source)
    assert get_display_ext(source) == ".png.zzzcomp"
    with decompressed(source) as path:
        assert path is None


@pytest.mark.parametrize(
    ["filename", "inner_ext", "display_ext"],
    [
        ("photo.png.gz", ".png", ".png.gz"),
        ("my.cool.Photo.PNG.XZ", ".png", ".png.xz"),
        ("bundle.tar.gz", None, ".tar.gz"),
        ("notes.final.gz", None, ".gz"),
        ("log.gz", None, ".gz"),
        ("photo.png", None, ".png"),
    ],
)
def test_inner_and_display_ext(filename: str, inner_ext: str | None, display_ext: str):
    assert get_inner_ext(Path(filename)) == inner_ext
    assert get_display_ext(Path(filename)) == display_ext


def test_decompress(tmp_path: Path):
    source = tmp_path / "notes.txt.gz"
    source.write_bytes(gzip.compress(b"x" * 1000))  # Decompresses to exactly 1000 bytes

    # A size equal to the limit is allowed (1000)
    assert decompress(source, tmp_path / "notes.txt", max_size=1000)
    # The full contents were written
    assert (tmp_path / "notes.txt").read_bytes() == b"x" * 1000
    # A size over the limit is not allowed (999)
    assert not decompress(source, tmp_path / "capped.txt", max_size=999)


def test_decompressed_uncompressed_file(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_bytes(b"plain")

    with decompressed(source) as path:
        assert path == source


def test_decompressed_compressed_file(tmp_path: Path):
    source = tmp_path / "my.notes.txt.gz"
    source.write_bytes(gzip.compress(b"x" * 1000))

    with decompressed(source) as path:
        assert path is not None
        assert path.name == "my.notes.txt"
        assert path.read_bytes() == b"x" * 1000

    assert not path.exists()


def test_decompressed_too_large(tmp_path: Path):
    source = tmp_path / "notes.txt.gz"
    source.write_bytes(gzip.compress(b"x" * 1000))

    with decompressed(source, max_size=999) as path:
        assert path is None


def test_decompressed_corrupt_file(tmp_path: Path):
    source = tmp_path / "photo.png.gz"
    source.write_bytes(b"not gzip data")

    with decompressed(source) as path:
        assert path is None
