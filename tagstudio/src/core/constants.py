VERSION: str = "9.4.1"  # Major.Minor.Patch
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
