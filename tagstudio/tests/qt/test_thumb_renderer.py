# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import io
from pathlib import Path

from PIL import Image
from src.qt.widgets.thumb_renderer import ThumbRenderer
from syrupy.extensions.image import PNGImageSnapshotExtension


def test_epub_preview(cwd, snapshot):
    # sample.epub, aka "Garrish, Matt. Epub 3 Best Practices (Excerpt). O’Reilly, 2013."
    # provided by https://idpf.github.io/epub3-samples/30/samples.html
    # under the CC-BY-SA 3.0 license: https://creativecommons.org/licenses/by-sa/3.0/
    file_path: Path = cwd / "fixtures" / "sample.epub"
    tr = ThumbRenderer()
    img: Image.Image = tr._epub_cover(file_path)

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    assert img_bytes.read() == snapshot(extension_class=PNGImageSnapshotExtension)
