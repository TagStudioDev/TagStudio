# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import io
from pathlib import Path

from PIL import Image
from src.qt.widgets.thumb_renderer import ThumbRenderer
from syrupy.extensions.image import PNGImageSnapshotExtension


def test_odt_preview(cwd, snapshot):
    file_path: Path = cwd / "fixtures" / "sample.odt"
    renderer = ThumbRenderer()
    img: Image.Image = renderer._open_doc_thumb(file_path)

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    assert img_bytes.read() == snapshot(extension_class=PNGImageSnapshotExtension)


def test_ods_preview(cwd, snapshot):
    file_path: Path = cwd / "fixtures" / "sample.ods"
    renderer = ThumbRenderer()
    img: Image.Image = renderer._open_doc_thumb(file_path)

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    assert img_bytes.read() == snapshot(extension_class=PNGImageSnapshotExtension)
