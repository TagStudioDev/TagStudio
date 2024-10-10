# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path

from PIL import Image
from src.qt.widgets.thumb_renderer import ThumbRenderer


def test_epub_to_png():
    # sample.epub, aka "Garrish, Matt. Epub 3 Best Practices (Excerpt). O’Reilly, 2013."
    # provided by https://idpf.github.io/epub3-samples/30/samples.html
    # under the CC-BY-SA 3.0 license: https://creativecommons.org/licenses/by-sa/3.0/
    file_path = Path(__file__).parents[1] / "fixtures" / "sample.epub"
    tr = ThumbRenderer()
    cover_image: Image.Image = tr._epub_cover(file_path)

    assert cover_image is not None
