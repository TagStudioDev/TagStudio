# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from collections.abc import Callable
from pathlib import Path

from PIL import Image
from PySide6.QtGui import QPixmap

class ResourceManager:
    # Methods
    get: Callable[..., Image.Image | bytes | None]
    get_path: Callable[..., Path | None]

    # Attributes
    _map: dict[str, dict[str, str]]
    _cache: dict[str, bytes | str | Image.Image | QPixmap]
    _instance: ResourceManager | None

    # Resources IDs from "resources.json"
    adobe_illustrator: Image.Image
    adobe_photoshop: Image.Image
    affinity_photo: Image.Image
    archive: Image.Image
    audio: Image.Image
    broken_link_icon: Image.Image
    bxs_left_arrow: Image.Image
    bxs_right_arrow: Image.Image
    copy: Image.Image
    database: Image.Image
    document: Image.Image
    dupe_file_stat: Image.Image
    ebook: Image.Image
    edit: Image.Image
    file_generic: Image.Image
    font: Image.Image
    icon: Image.Image
    ignored_stat: Image.Image
    ignored: Image.Image
    image_vector: Image.Image
    image: Image.Image
    material: Image.Image
    model: Image.Image
    mute_icon: Image.Image
    pause_icon: Image.Image
    presentation: Image.Image
    program: Image.Image
    shader: Image.Image
    shortcut: Image.Image
    splash_95: QPixmap
    splash_aurora: QPixmap
    splash_classic: QPixmap
    splash_goo_gears: QPixmap
    spreadsheet: Image.Image
    text: Image.Image
    thumb_loading: Image.Image
    trash: Image.Image
    ts_logo_text_color: Image.Image
    ts_logo_text_mono: Image.Image
    unlinked_stat: Image.Image
    video: Image.Image
    volume_icon: Image.Image
