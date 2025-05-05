# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import contextlib
import math
import typing
from datetime import datetime as dt
from pathlib import Path

import structlog
from PIL import Image

from tagstudio.core.constants import THUMB_CACHE_NAME, TS_FOLDER_NAME
from tagstudio.core.singleton import Singleton

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from tagstudio.core.library import Library

logger = structlog.get_logger(__name__)


class CacheManager(metaclass=Singleton):
    FOLDER_SIZE = 10000000  # Each cache folder assumed to be 10 MiB
    size_limit = 500000000  # 500 MiB default

    folder_dict: dict[Path, int] = {}

    def __init__(self):
        self.lib: Library | None = None
        self.last_lib_path: Path | None = None

    @staticmethod
    def clear_cache(library_dir: Path | None) -> bool:
        """Clear all files and folders within the cached folder.

        Returns:
            bool: True if successfully deleted, else False.
        """
        cleared = True

        if library_dir:
            tree: Path = library_dir / TS_FOLDER_NAME / THUMB_CACHE_NAME

            for folder in tree.glob("*"):
                for file in folder.glob("*"):
                    # NOTE: On macOS with non-native file systems, this will commonly raise
                    # FileNotFound errors due to trying to delete "._" files that have
                    # already been deleted: https://bugs.python.org/issue29699
                    with contextlib.suppress(FileNotFoundError):
                        file.unlink()
                try:
                    folder.rmdir()
                    with contextlib.suppress(KeyError):
                        CacheManager.folder_dict.pop(folder)
                except Exception as e:
                    logger.error(
                        "[CacheManager] Couldn't unlink empty cache folder!",
                        error=e,
                        folder=folder,
                        tree=tree,
                    )

            for _ in tree.glob("*"):
                cleared = False

            if cleared:
                logger.info("[CacheManager] Cleared cache!")
            else:
                logger.error("[CacheManager] Couldn't delete cache!", tree=tree)

        return cleared

    def set_library(self, library):
        """Set the TagStudio library for the cache manager."""
        self.lib = library
        self.last_lib_path = self.lib.library_dir
        if library.library_dir:
            self.check_folder_status()

    def cache_dir(self) -> Path | None:
        """Return the current cache directory, not including folder slugs."""
        if not self.lib.library_dir:
            return None
        return Path(self.lib.library_dir / TS_FOLDER_NAME / THUMB_CACHE_NAME)

    def save_image(self, image: Image.Image, path: Path, mode: str = "RGBA"):
        """Save an image to the cache."""
        folder = self.get_current_folder()
        if folder:
            image_path: Path = folder / path
            image.save(image_path, mode=mode)
            with contextlib.suppress(KeyError):
                CacheManager.folder_dict[folder] += image_path.stat().st_size

    def check_folder_status(self):
        """Check the status of the cache folders.

        This includes registering existing ones and creating new ones if needed.
        """
        if (
            (self.last_lib_path != self.lib.library_dir)
            or not self.cache_dir()
            or not self.cache_dir().exists()
        ):
            self.register_existing_folders()

        def create_folder() -> Path | None:
            """Create a new cache folder."""
            if not self.lib.library_dir:
                return None
            folder_path = Path(self.cache_dir() / str(math.floor(dt.timestamp(dt.now()))))
            logger.info("[CacheManager] Creating new folder", folder=folder_path)
            try:
                folder_path.mkdir(exist_ok=True)
            except NotADirectoryError:
                logger.error("[CacheManager] Not a directory", path=folder_path)
            return folder_path

        # Get size of most recent folder, if any exist.
        if CacheManager.folder_dict:
            last_folder = sorted(CacheManager.folder_dict.keys())[-1]

            if CacheManager.folder_dict[last_folder] > CacheManager.FOLDER_SIZE:
                new_folder = create_folder()
                CacheManager.folder_dict[new_folder] = 0
        else:
            new_folder = create_folder()
            CacheManager.folder_dict[new_folder] = 0

    def get_current_folder(self) -> Path:
        """Get the current cache folder path that should be used."""
        self.check_folder_status()
        self.cull_folders()

        return sorted(CacheManager.folder_dict.keys())[-1]

    def register_existing_folders(self):
        """Scan and register any pre-existing cache folders with the most recent size."""
        self.last_lib_path = self.lib.library_dir
        CacheManager.folder_dict.clear()

        if self.last_lib_path:
            # Ensure thumbnail cache path exists.
            self.cache_dir().mkdir(exist_ok=True)
            # Registers any existing folders and counts the capacity of the most recent one.
            for f in sorted(self.cache_dir().glob("*")):
                if f.is_dir():
                    # A folder is found. Add it to the class dict.BlockingIOError
                    CacheManager.folder_dict[f] = 0
            CacheManager.folder_dict = dict(
                sorted(CacheManager.folder_dict.items(), key=lambda kv: kv[0])
            )

            if CacheManager.folder_dict:
                last_folder = sorted(CacheManager.folder_dict.keys())[-1]
                for f in last_folder.glob("*"):
                    if not f.is_dir():
                        with contextlib.suppress(KeyError):
                            CacheManager.folder_dict[last_folder] += f.stat().st_size

    def cull_folders(self):
        """Remove folders and their cached context based on size or age limits."""
        # Ensure that the user's configured size limit isn't less than the internal folder size.
        size_limit = max(CacheManager.size_limit, CacheManager.FOLDER_SIZE)

        if len(CacheManager.folder_dict) > (size_limit / CacheManager.FOLDER_SIZE):
            f = sorted(CacheManager.folder_dict.keys())[0]
            folder = self.cache_dir() / f
            logger.info("[CacheManager] Removing folder due to size limit", folder=folder)

            for file in folder.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(
                        "[CacheManager] Couldn't cull file inside of folder!",
                        error=e,
                        file=file,
                        folder=folder,
                    )
            try:
                folder.rmdir()
                with contextlib.suppress(KeyError):
                    CacheManager.folder_dict.pop(f)
                self.cull_folders()
            except Exception as e:
                logger.error("[CacheManager] Couldn't cull folder!", error=e, folder=folder)
                pass
