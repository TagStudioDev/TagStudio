# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from pathlib import Path

import structlog
from send2trash import send2trash

logger = structlog.get_logger(__name__)


def delete_file(path: str | Path) -> bool:
    """Send a file to the system trash.

    Args:
        path (str | Path): The path of the file to delete.
    """
    _path = Path(path)
    try:
        logger.info(f"[delete_file] Sending to Trash: {_path}")
        send2trash(_path)
        return True
    except PermissionError as e:
        logger.error(f"[delete_file][ERROR] PermissionError: {e}")
    except FileNotFoundError:
        logger.error(f"[delete_file][ERROR] File Not Found: {_path}")
    except Exception as e:
        logger.error(e)
    return False
