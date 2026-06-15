# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from PIL import Image

from tagstudio.qt.previews.renderer import ThumbRenderer


def _write_webp_archive(archive_path: Path) -> None:
    image_data = BytesIO()
    Image.new("RGB", (2, 2), "red").save(image_data, format="WEBP")

    with ZipFile(archive_path, "w") as archive:
        archive.writestr("cover.webp", image_data.getvalue())


def test_archive_thumb_extracts_webp_image(tmp_path: Path):
    archive_path = tmp_path / "webp_only.zip"
    _write_webp_archive(archive_path)

    thumbnail = ThumbRenderer._archive_thumb(archive_path, ".zip")

    assert thumbnail is not None
    assert thumbnail.size == (2, 2)


def test_epub_cover_extracts_webp_image_from_cbz(tmp_path: Path):
    archive_path = tmp_path / "webp_only.cbz"
    _write_webp_archive(archive_path)

    thumbnail = ThumbRenderer._epub_cover(archive_path, ".cbz")

    assert thumbnail is not None
    assert thumbnail.size == (2, 2)
