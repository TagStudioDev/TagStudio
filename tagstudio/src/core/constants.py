VERSION: str = "9.3.2"  # Major.Minor.Patch
VERSION_BRANCH: str = ""  # Usually "" or "Pre-Release"

# The folder & file names where TagStudio keeps its data relative to a library.
TS_FOLDER_NAME: str = ".TagStudio"
BACKUP_FOLDER_NAME: str = "backups"
COLLAGE_FOLDER_NAME: str = "collages"
LIBRARY_FILENAME: str = "ts_library.json"

# TODO: Turn this whitelist into a user-configurable blacklist.
IMAGE_TYPES: list[str] = [
    ".png",
    ".jpg",
    ".jpeg",
    ".jpg_large",
    ".jpeg_large",
    ".jfif",
    ".gif",
    ".tif",
    ".tiff",
    ".heic",
    ".heif",
    ".webp",
    ".bmp",
    ".svg",
    ".avif",
    ".apng",
    ".jp2",
    ".j2k",
    ".jpg2",
]
RAW_IMAGE_TYPES: list[str] = [
    ".raw",
    ".dng",
    ".rw2",
    ".nef",
    ".arw",
    ".crw",
    ".cr2",
    ".cr3",
]
VIDEO_TYPES: list[str] = [
    ".mp4",
    ".webm",
    ".mov",
    ".hevc",
    ".mkv",
    ".avi",
    ".wmv",
    ".flv",
    ".gifv",
    ".m4p",
    ".m4v",
    ".3gp",
]
AUDIO_TYPES: list[str] = [
    ".mp3",
    ".mp4",
    ".mpeg4",
    ".m4a",
    ".aac",
    ".wav",
    ".flac",
    ".alac",
    ".wma",
    ".ogg",
    ".aiff",
]
DOC_TYPES: list[str] = [
    ".txt",
    ".rtf",
    ".md",
    ".doc",
    ".docx",
    ".pdf",
    ".tex",
    ".odt",
    ".pages",
]
PLAINTEXT_TYPES: list[str] = [
    ".txt",
    ".md",
    ".css",
    ".html",
    ".xml",
    ".json",
    ".js",
    ".ts",
    ".ini",
    ".htm",
    ".csv",
    ".php",
    ".sh",
    ".bat",
]
SPREADSHEET_TYPES: list[str] = [".csv", ".xls", ".xlsx", ".numbers", ".ods"]
PRESENTATION_TYPES: list[str] = [".ppt", ".pptx", ".key", ".odp"]
ARCHIVE_TYPES: list[str] = [
    ".zip",
    ".rar",
    ".tar",
    ".tar",
    ".gz",
    ".tgz",
    ".7z",
    ".s7z",
]
PROGRAM_TYPES: list[str] = [".exe", ".app"]
SHORTCUT_TYPES: list[str] = [".lnk", ".desktop", ".url"]

ALL_FILE_TYPES: list[str] = (
    IMAGE_TYPES
    + VIDEO_TYPES
    + AUDIO_TYPES
    + DOC_TYPES
    + SPREADSHEET_TYPES
    + PRESENTATION_TYPES
    + ARCHIVE_TYPES
    + PROGRAM_TYPES
    + SHORTCUT_TYPES
)

BOX_FIELDS = ["tag_box", "text_box"]
TEXT_FIELDS = ["text_line", "text_box"]
DATE_FIELDS = ["datetime"]

DEFAULT_TAG_COLOR = "#f2f1f8"
DEFAULT_FAVORITE_COLOR = "#ffd63d"
DEFAULT_ARCHIVED_COLOR = "#e22c3c"

LEGACY_TAG_COLORS: dict = {
    "": "#1e1e1e",
    "black": "#111018",
    "dark gray": "#24232a",
    "gray": "#53525a",
    "light gray": "#aaa9b0",
    "white": "#f2f1f8",
    "light pink": "#ff99c4",
    "pink": "#ff99c4",
    "red": "#e22c3c",
    "red orange": "#e83726",
    "orange": "#ed6022",
    "yellow orange": "#fa9a2c",
    "yellow": "#ffd63d",
    "lime": "#92e649",
    "light green": "#85ec76",
    "mint": "#4aed90",
    "green": "#28bb48",
    "teal": "#1ad9b2",
    "cyan": "#49e4d5",
    "light blue": "#55bbf6",
    "blue": "#3b87f0",
    "blue violet": "#5948f2",
    "violet": "#874ff5",
    "purple": "#bb4ff0",
    "lavender": "#ad8eef",
    "berry": "#9f2aa7",
    "magenta": "#e83726",
    "salmon": "#f65848",
    "auburn": "#a13220",
    "dark brown": "#4c2315",
    "brown": "#823216",
    "light brown": "#be5b2d",
    "blonde": "#efc664",
    "peach": "#f1c69c",
    "warm gray": "#625550",
    "cool gray": "#515768",
    "olive": "#4c652e",
}

TAG_FAVORITE = 1
TAG_ARCHIVED = 0
