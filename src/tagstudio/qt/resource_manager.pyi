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
    about_bg: QPixmap
    adobe_illustrator: Image.Image
    adobe_photoshop: Image.Image
    affinity_photo: Image.Image
    alert: QPixmap
    archived_icon: bytes
    archive: Image.Image
    arrow_right: bytes
    arrow_right_bottom: bytes
    audio: Image.Image
    broken_link_icon: Image.Image
    bxs_left_arrow: Image.Image
    bxs_right_arrow: Image.Image
    card_text: bytes
    card_text_outline: bytes
    chevron_down: bytes
    colors_icon: bytes
    colors_icon_solid: bytes
    copy: Image.Image
    database: Image.Image
    document: Image.Image
    dupe_file_stat: Image.Image
    ebook: Image.Image
    edit: Image.Image
    entries_icon: bytes
    entries_icon_solid: bytes
    eye: bytes
    eye_closed: bytes
    favorite_icon: bytes
    file_generic: Image.Image
    file_system_icons_view_icon: bytes
    file_system_list_view_icon: bytes
    font: Image.Image
    gallery_view_icon: bytes
    grid_view_icon: bytes
    hint_field_add: Image.Image
    hint_field_create: Image.Image
    hint_field_issue: Image.Image
    hint_tag_add: Image.Image
    hint_tag_added: Image.Image
    hint_tag_create: Image.Image
    hint_tag_issue: Image.Image
    icon: Image.Image
    ignored_stat: Image.Image
    ignored: Image.Image
    image_vector: Image.Image
    image: Image.Image
    info_outline: bytes
    info_solid: bytes
    library_stats_icon: bytes
    library_stats_icon_solid: bytes
    list_view_icon: bytes
    masonry_view_icon: bytes
    material: Image.Image
    model: Image.Image
    mute_icon: Image.Image
    pause_icon: Image.Image
    pinned_tags_icon_solid: bytes
    plaintext: Image.Image
    presentation: Image.Image
    preview_icon_solid: bytes
    program: Image.Image
    recent_tags_icon_solid: bytes
    settings_icon: bytes
    settings_icon_solid: bytes
    shader: Image.Image
    shortcut: Image.Image
    sort_alphabetical_ascending_icon: bytes
    sort_alphabetical_descending_icon: bytes
    sort_calendar_ascending_icon: bytes
    sort_calendar_descending_icon: bytes
    sort_numeric_ascending_icon: bytes
    sort_numeric_descending_icon: bytes
    sort_random_icon: bytes
    splash_95: QPixmap
    splash_aurora: QPixmap
    splash_classic: QPixmap
    splash_goo_gears: QPixmap
    spreadsheet: Image.Image
    sync_icon: bytes
    tag_search_icon_solid: bytes
    tags_icon: bytes
    tags_icon_solid: bytes
    thumb_loading: Image.Image
    top_tags_icon_solid: bytes
    trash: Image.Image
    ts_logo_text_color: Image.Image
    ts_logo_text_mono: Image.Image
    unlinked_stat: Image.Image
    video: Image.Image
    volume_icon: Image.Image
