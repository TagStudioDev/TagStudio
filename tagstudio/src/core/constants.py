from enum import Enum

VERSION: str = "9.3.2"  # Major.Minor.Patch
VERSION_BRANCH: str = ""  # Usually "" or "Pre-Release"

# The folder & file names where TagStudio keeps its data relative to a library.
TS_FOLDER_NAME: str = ".TagStudio"
BACKUP_FOLDER_NAME: str = "backups"
COLLAGE_FOLDER_NAME: str = "collages"
LIBRARY_FILENAME: str = "ts_library.json"

FONT_SAMPLE_TEXT: str = (
    """ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?@$%(){}[]"""
)
FONT_SAMPLE_SIZES: list[int] = [10, 15, 20]

TAG_FAVORITE = 1
TAG_ARCHIVED = 0


class LibraryPrefs(Enum):
    IS_EXCLUDE_LIST = True
    EXTENSION_LIST: list[str] = [".json", ".xmp", ".aae"]
    PAGE_SIZE: int = 500
    DB_VERSION: int = 1
