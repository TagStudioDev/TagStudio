import enum

TS_FOLDER_NAME = ".TagStudio"


class OpenStatus(enum.IntEnum):
    NOT_FOUND = 0
    SUCCESS = 1
    CORRUPTED = 2
