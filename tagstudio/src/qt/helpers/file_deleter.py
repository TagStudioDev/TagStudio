# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
from pathlib import Path

from send2trash import send2trash

logging.basicConfig(format="%(message)s", level=logging.INFO)


def delete_file(path: str | Path) -> bool:
    """Send a file to the system trash.

    Args:
        path (str | Path): The path of the file to delete.
    """
    _path = Path(path)
    try:
        logging.info(f"[delete_file] Sending to Trash: {_path}")
        send2trash(_path)
        return True
    except PermissionError as e:
        logging.error(f"[delete_file][ERROR] PermissionError: {e}")
    except FileNotFoundError:
        logging.error(f"[delete_file][ERROR] File Not Found: {_path}")
    except Exception as e:
        logging.error(e)
    return False
