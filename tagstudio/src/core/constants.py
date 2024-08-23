VERSION: str = "9.3.2"  # Major.Minor.Patch
VERSION_BRANCH: str = ""  # Usually "" or "Pre-Release"

# The folder & file names where TagStudio keeps its data relative to a library.
TS_FOLDER_NAME: str = ".TagStudio"
BACKUP_FOLDER_NAME: str = "backups"
COLLAGE_FOLDER_NAME: str = "collages"
LIBRARY_FILENAME: str = "ts_library.json"

# TODO: Turn this whitelist into a user-configurable blacklist.
IMAGE_TYPES: list[str] = [
    ".apng",
    ".avif",
    ".bmp",
    ".gif",
    ".heic",
    ".heif",
    ".j2k",
    ".jfif",
    ".jp2",
    ".jpeg",
    ".jpeg_large",
    ".jpg",
    ".jpg2",
    ".jpg_large",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
]
RAW_IMAGE_TYPES: list[str] = [
    ".arw",
    ".cr2",
    ".cr3",
    ".crw",
    ".dng",
    ".nef",
    ".raw",
    ".rw2",
]
VIDEO_TYPES: list[str] = [
    ".3gp",
    ".avi",
    ".flv",
    ".gifv",
    ".hevc",
    ".m4p",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".webm",
    ".wmv",
]
AUDIO_TYPES: list[str] = [
    ".aac",
    ".aiff",
    ".alac",
    ".flac",
    ".m4a",
    ".mp3",
    ".mp4",
    ".mpeg4",
    ".ogg",
    ".wav",
    ".wma",
]
DOC_TYPES: list[str] = [
    ".doc",
    ".docx",
    ".md",
    ".odt",
    ".pages",
    ".pdf",
    ".rtf",
    ".tex",
    ".txt",
]
PLAINTEXT_TYPES: list[str] = [
    ".bat",
    ".css",
    ".csv",
    ".htm",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".php",
    ".sh",
    ".ts",
    ".txt",
    ".xml",
]
SPREADSHEET_TYPES: list[str] = [".csv", ".numbers", ".ods", ".xls", ".xlsx"]
PRESENTATION_TYPES: list[str] = [".key", ".odp", ".ppt", ".pptx"]
ARCHIVE_TYPES: list[str] = [
    ".7z",
    ".gz",
    ".rar",
    ".s7z",
    ".tar",
    ".tar",
    ".tgz",
    ".zip",
]
PROGRAM_TYPES: list[str] = [".app", ".exe"]
SHORTCUT_TYPES: list[str] = [".desktop", ".lnk", ".url"]

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

TAG_COLORS = [
    "",
    "black",
    "dark gray",
    "gray",
    "light gray",
    "white",
    "light pink",
    "pink",
    "red",
    "red orange",
    "orange",
    "yellow orange",
    "yellow",
    "lime",
    "light green",
    "mint",
    "green",
    "teal",
    "cyan",
    "light blue",
    "blue",
    "blue violet",
    "violet",
    "purple",
    "lavender",
    "berry",
    "magenta",
    "salmon",
    "auburn",
    "dark brown",
    "brown",
    "light brown",
    "blonde",
    "peach",
    "warm gray",
    "cool gray",
    "olive",
]

TAG_FAVORITE = 1
TAG_ARCHIVED = 0
