# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import platform
import shutil
from datetime import datetime
from enum import IntEnum
from pathlib import Path

import structlog
from platformdirs import user_config_path
from pydantic import field_validator

from tagstudio.core.utils.data_file import BaseDataFile

logger = structlog.get_logger(__name__)

DEFAULT_APP_SETTINGS_PATH = (
    user_config_path("TagStudio", appauthor=False, roaming=True) / "app_settings.toml"
)
_LEGACY_SETTINGS_PATH = (
    Path.home() / "Appdata" / "Roaming" / "TagStudio" / "settings.toml"
    if platform.system() == "Windows"
    else Path.home() / ".config" / "TagStudio" / "settings.toml"
)

DEFAULT_THUMB_CACHE_SIZE = 500  # Number in MiB
MIN_THUMB_CACHE_SIZE = 10  # Number in MiB

# See: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp-saving
DEFAULT_CACHED_THUMB_QUALITY = 80  # WebP Compression Quality
MIN_CACHED_THUMB_RES = 32  # Pixels
MAX_CACHED_THUMB_RES = 1024  # Pixels
DEFAULT_CACHED_THUMB_RES = 256  # Pixels

PAGE_SIZES = (50, 100, 250, 500, 1000, 2500, 5000)


class ShowLabelOption(IntEnum):
    """Used for common options that can show labels in different states."""

    ALWAYS = 0
    ON_HOVER = 1
    NEVER = 2


class ThemeOption(IntEnum):
    """Options for the "theme" setting."""

    DARK = 0
    LIGHT = 1
    SYSTEM = 2
    DEFAULT = SYSTEM


class ShowFilepathOption(IntEnum):
    """Options for the "show_filepath" setting."""

    SHOW_FULL_PATHS = 0
    SHOW_RELATIVE_PATHS = 1
    SHOW_FILENAMES_ONLY = 2
    DEFAULT = SHOW_RELATIVE_PATHS


class TagClickActionOption(IntEnum):
    """Options for the "tag_click_action" setting."""

    OPEN_EDIT = 0
    SET_SEARCH = 1
    ADD_TO_SEARCH = 2
    DEFAULT = OPEN_EDIT


# NOTE: pydantic also has a BaseSettings class (from pydantic-settings) that allows any settings
# properties to be overwritten with environment variables. As TagStudio is not currently using
# environment variables, this was not based on that, but that may be useful in the future.
class AppSettings(BaseDataFile):
    """Application settings file for TagStudio."""

    language: str = "en"
    open_last_loaded_on_startup: bool = True
    generate_thumbs: bool = True
    thumb_cache_size: float = DEFAULT_THUMB_CACHE_SIZE
    cached_thumb_quality: int = DEFAULT_CACHED_THUMB_QUALITY
    cached_thumb_resolution: int = DEFAULT_CACHED_THUMB_RES
    autoplay: bool = True
    scan_files_on_open: bool = True
    loop: bool = True
    show_filenames_in_grid: bool = True
    show_extensions_in_grid: ShowLabelOption = ShowLabelOption.ALWAYS
    show_durations_in_grid: ShowLabelOption = ShowLabelOption.ALWAYS
    page_size: int = 100
    infinite_scroll: bool = True
    show_filepath: ShowFilepathOption = ShowFilepathOption.DEFAULT
    tag_click_action: TagClickActionOption = TagClickActionOption.DEFAULT
    edit_tag_on_create: bool = False
    edit_field_on_add: bool = True
    keep_suggest_boxes_open: bool = True
    dont_create_items_on_enter: bool = False
    sort_added_tags_last: bool = True
    invert_suggest_box_scroll: bool = False
    theme: ThemeOption = ThemeOption.SYSTEM
    pill_shaped_tags: bool = True
    circular_badges: bool = True
    windows_start_command: bool = False

    date_format: str = "%x"
    hour_format: bool = True
    zero_padding: bool = True

    @field_validator("page_size")
    @classmethod
    def _round_page_size(cls, page_size: int) -> int:
        """Round page size in settings file to the closest preconfigured internal size.

        NOTE: Implicitly used by pydantic.
        """
        return min(PAGE_SIZES, key=lambda size: abs(size - page_size))

    @property
    def datetime_format(self) -> str:
        date_format = self.date_format
        is_24h = self.hour_format
        hour_format = "%H:%M:%S" if is_24h else "%I:%M:%S %p"
        zero_padding = self.zero_padding
        zero_padding_symbol = ""

        if not zero_padding:
            zero_padding_symbol = "#" if platform.system() == "Windows" else "-"
            date_format = date_format.replace("%d", f"%{zero_padding_symbol}d").replace(
                "%m", f"%{zero_padding_symbol}m"
            )
            hour_format = hour_format.replace("%H", f"%{zero_padding_symbol}H").replace(
                "%I", f"%{zero_padding_symbol}I"
            )
        return f"{date_format}, {hour_format}"

    def format_datetime(self, dt: datetime) -> str:
        return datetime.strftime(dt, self.datetime_format)


def migrate_legacy_settings(
    legacy_path: Path = _LEGACY_SETTINGS_PATH, path: Path = DEFAULT_APP_SETTINGS_PATH
) -> None:
    """Move the legacy settings.toml file to the current app_settings.toml location."""
    if path.exists() or not legacy_path.exists():
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(legacy_path, path)
    except OSError as error:
        logger.warning(
            "[Settings] Couldn't move legacy settings file",
            legacy_path=legacy_path,
            path=path,
            error=error,
        )
        return
    logger.info("[Settings] Moved legacy settings file", legacy_path=legacy_path, path=path)
