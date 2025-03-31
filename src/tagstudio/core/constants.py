# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

VERSION: str = "9.5.2"  # Major.Minor.Patch
VERSION_BRANCH: str = ""  # Usually "" or "Pre-Release"

# The folder & file names where TagStudio keeps its data relative to a library.
TS_FOLDER_NAME: str = ".TagStudio"
BACKUP_FOLDER_NAME: str = "backups"
COLLAGE_FOLDER_NAME: str = "collages"
THUMB_CACHE_NAME: str = "thumbs"

FONT_SAMPLE_TEXT: str = (
    """ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?@$%(){}[]"""
)
FONT_SAMPLE_SIZES: list[int] = [10, 15, 20]

# NOTE: These were the field IDs used for the "Tags", "Content Tags", and "Meta Tags" fields inside
# the legacy JSON database. These are used to help migrate libraries from JSON to SQLite.
LEGACY_TAG_FIELD_IDS: set[int] = {6, 7, 8}

TAG_ARCHIVED = 0
TAG_FAVORITE = 1
TAG_META = 2
RESERVED_TAG_START = 0
RESERVED_TAG_END = 999

RESERVED_NAMESPACE_PREFIX = "tagstudio"
