# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

# pyright: reportPrivateUsage=false


from compression import gzip, lzma
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from tagstudio.core.enums import Theme
from tagstudio.previews.file_renderer import FileRenderer


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


def test_render_decompressed_without_inner_extension(tmp_path: Path):
    source = tmp_path / "log.gz"
    source.write_bytes(gzip.compress(b"plain text"))

    assert (
        FileRenderer._render_decompressed(
            source, is_small=True, theme=Theme.DARK, size=(128, 128), dpi_scale=1.0
        )
        is None
    )
