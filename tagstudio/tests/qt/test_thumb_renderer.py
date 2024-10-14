# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import io
from pathlib import Path

from PIL import Image
from src.qt.widgets.thumb_renderer import ThumbRenderer
from syrupy.extensions.image import PNGImageSnapshotExtension


def test_pdf_preview(cwd, snapshot):
    file_path: Path = cwd / "fixtures" / "sample.pdf"
    renderer = ThumbRenderer()
    img: Image.Image = renderer._pdf_thumb(file_path, 200)

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    assert img_bytes.read() == snapshot(extension_class=PNGImageSnapshotExtension)


def test_svg_preview(cwd, snapshot):
    file_path: Path = cwd / "fixtures" / "sample.svg"
    renderer = ThumbRenderer()
    img: Image.Image = renderer._image_vector_thumb(file_path, 200)

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    assert img_bytes.read() == snapshot(extension_class=PNGImageSnapshotExtension)
