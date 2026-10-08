# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

# pyright: reportPrivateUsage=false


import tarfile
from collections.abc import Callable
from compression import bz2, gzip, lzma, zstd
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from tagstudio.core.enums import Theme
from tagstudio.previews.file_renderer import FileRenderer
from tagstudio.previews.renderers.archive import ArchivePreview


def _example_png_bytes() -> bytes:
    data = BytesIO()
    Image.new("RGBA", (40, 20), (255, 0, 0, 255)).save(data, "PNG")
    return data.getvalue()


@pytest.mark.parametrize("filename", ["photo.png.gz", "my.cool.photo.PNG.XZ"])
def test_render_decompressed(tmp_path: Path, filename: str):
    source = tmp_path / filename
    if filename.lower().endswith(".gz"):
        source.write_bytes(gzip.compress(_example_png_bytes()))
    else:
        source.write_bytes(lzma.compress(_example_png_bytes()))

    image = FileRenderer._render_decompressed(
        source, is_small=True, theme=Theme.DARK, size=(128, 128), dpi_scale=1.0
    )

    assert image is not None
    assert image.size == (40, 20)


def _example_tar_bytes() -> bytes:
    data = BytesIO()
    with tarfile.open(fileobj=data, mode="w") as tar:
        png = _example_png_bytes()
        info = tarfile.TarInfo("images/photo.png")
        info.size = len(png)
        tar.addfile(info, BytesIO(png))
    return data.getvalue()


@pytest.mark.parametrize(
    ["filename", "compress"],
    [
        ("bundle.tar.bz2", bz2.compress),
        ("bundle.tbz2", bz2.compress),
        ("bundle.tar.lzma", lambda data: lzma.compress(data, format=lzma.FORMAT_ALONE)),
        ("bundle.tlz", lambda data: lzma.compress(data, format=lzma.FORMAT_ALONE)),
        ("my.cool.bundle.tar.xz", lzma.compress),
        ("BUNDLE.TXZ", lzma.compress),
        ("bundle.tar.zst", zstd.compress),
        ("bundle.tzst", zstd.compress),
    ],
)
def test_render_compressed_tarball(
    tmp_path: Path, filename: str, compress: Callable[[bytes], bytes]
):
    source = tmp_path / filename
    source.write_bytes(compress(_example_tar_bytes()))

    assert FileRenderer._find_preview(source) is ArchivePreview
    image = ArchivePreview.render(
        source, is_small=True, theme=Theme.DARK, size=(128, 128), dpi_scale=1.0
    )

    assert image is not None
    assert image.size == (40, 20)


def test_render_decompressed_without_inner_extension(tmp_path: Path):
    source = tmp_path / "log.gz"
    source.write_bytes(gzip.compress(b"plain text"))

    assert (
        FileRenderer._render_decompressed(
            source, is_small=True, theme=Theme.DARK, size=(128, 128), dpi_scale=1.0
        )
        is None
    )
