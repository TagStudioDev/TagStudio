# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import os
from pathlib import Path
from platform import system

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
        logger.error(f"[delete_file] PermissionError: {e}")
    except FileNotFoundError:
        logger.error(f"[delete_file] File Not Found: {_path}")
    except OSError as e:
        if system() == "Darwin" and _path.exists():
            logger.info(
                f'[delete_file] Encountered "{e}" on macOS and file exists; '
                "Assuming it's on a network volume and proceeding to delete..."
            )
            return _hard_delete_file(_path)
        else:
            logger.error("[delete_file] OSError", error=e)
    except Exception as e:
        logger.error("[delete_file] Unknown Error", error_type=type(e).__name__, error=e)
    return False


def _hard_delete_file(path: Path) -> bool:
    """Hard delete a file from the system. Does NOT send to system trash.

    Args:
        path (str | Path): The path of the file to delete.
    """
    try:
        os.remove(path)
        return True
    except Exception as e:
        logger.error("[hard_delete_file] Error", error_type=type(e).__name__, error=e)
        return False
