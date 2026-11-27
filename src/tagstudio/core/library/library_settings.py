# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from enum import IntEnum

from pydantic import field_validator

from tagstudio.core.library.alchemy.enums import SortingModeEnum
from tagstudio.core.utils.data_file import BaseDataFile

DEFAULT_THUMB_CACHE_SIZE = 500  # Number in MiB
MIN_THUMB_CACHE_SIZE = 10  # Number in MiB

# See: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp-saving
DEFAULT_CACHED_THUMB_QUALITY = 80  # WebP Compression Quality
MIN_CACHED_THUMB_RES = 32  # Pixels
MAX_CACHED_THUMB_RES = 1024  # Pixels
DEFAULT_CACHED_THUMB_RES = 256  # Pixels

MIN_THUMB_SIZE = 72
MAX_THUMB_SIZE = 240
THUMB_SIZE_STEP = 24
DEFAULT_THUMB_SIZE = 120

PAGE_SIZES = (50, 100, 250, 500, 1000, 2500, 5000)


class ShowLabelOption(IntEnum):
    """Used for common options that can show labels in different states."""

    ALWAYS = 0
    ON_HOVER = 1
    NEVER = 2


class LibrarySettings(BaseDataFile):
    """Library settings file for TagStudio."""

    generate_thumbs: bool = True
    thumb_cache_size: float = DEFAULT_THUMB_CACHE_SIZE
    cached_thumb_quality: int = DEFAULT_CACHED_THUMB_QUALITY
    cached_thumb_resolution: int = DEFAULT_CACHED_THUMB_RES
    sync_on_open: bool = True
    thumb_size: int = DEFAULT_THUMB_SIZE
    show_filenames: bool = True
    show_extensions: ShowLabelOption = ShowLabelOption.ALWAYS
    show_durations: ShowLabelOption = ShowLabelOption.ALWAYS
    page_size: int = 100
    infinite_scroll: bool = True
    sorting_mode: SortingModeEnum = SortingModeEnum.DATE_ADDED
    sort_ascending: bool = False
    show_hidden_entries: bool = False

    @field_validator("page_size")
    @classmethod
    def _round_page_size(cls, page_size: int) -> int:
        """Round page size in settings file to the closest preconfigured internal size.

        NOTE: Implicitly used by pydantic.
        """
        return min(PAGE_SIZES, key=lambda size: abs(size - page_size))
