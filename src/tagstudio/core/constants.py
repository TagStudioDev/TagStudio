# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from importlib.metadata import version

VERSION: str = version("tagstudio")
BUILD_TYPE: str = ""  # Usually "", "app.nightly", or "app.pre_release"
COPYRIGHT_YEARS: str = "2021-2026"
COPYRIGHT: str = f"© {COPYRIGHT_YEARS} Travis Abendshien & TagStudio Contributors"
COPYRIGHT_COMPACT: str = f"© {COPYRIGHT_YEARS} Travis Abendshien\n& TagStudio Contributors"

GITHUB_REPO_URL = "https://github.com/TagStudioDev/TagStudio"
GITHUB_RELEASE_URL = "https://github.com/TagStudioDev/TagStudio/releases/latest"
DOCS_URL = "https://docs.tagstud.io"
FFMPEG_HELP_URL = "https://docs.tagstud.io/help/ffmpeg"
DISCORD_URL = "https://discord.com/invite/hRNnVKhF2G"

# The folder & file names where TagStudio keeps its data relative to a library.
TS_FOLDER_NAME: str = ".TagStudio"
BACKUP_FOLDER_NAME: str = "backups"
COLLAGE_FOLDER_NAME: str = "collages"
IGNORE_NAME: str = ".ts_ignore"
THUMB_CACHE_NAME: str = "thumbs"

FONT_SAMPLE_TEXT: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?@$%(){}[]"
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
