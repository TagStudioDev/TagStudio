# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import contextlib
import math
from datetime import datetime as dt
from pathlib import Path

import structlog
from PIL import (
    Image,
)
from src.core.constants import THUMB_CACHE_NAME, TS_FOLDER_NAME

logger = structlog.get_logger(__name__)


class CacheManager:
    FOLDER_SIZE = 100000000  # Each cache folder assumed to be 100 MiB

    def __init__(self):
        self.lib = None
        self.last_lib_path = None
        self.folder_dict: dict[Path, int] = {}

        self.size_limit = 500000000  # 500 MiB # TODO: Pull this from config
        # self.age_limit = 172800  # 2 days # TODO: Pull this from config

    def set_library(self, library):
        """Set the TagStudio library for the cache manager."""
        self.lib = library
        self.last_lib_path = self.lib.library_dir
        if library.library_dir:
            self.is_init = False
            self.check_folder_status()

    def cache_dir(self) -> Path:
        """Return the current cache directory, not including folder slugs."""
        if not self.lib.library_dir:
            return None
        return Path(self.lib.library_dir / TS_FOLDER_NAME / THUMB_CACHE_NAME)

    def save_image(self, image: Image.Image, path: Path, mode: str = "RGBA"):
        """Save an image to the cache."""
        folder = self.get_current_folder()
        image_path: Path = folder / path
        image.save(image_path, mode=mode)
        self.folder_dict[folder] += image_path.stat().st_size

    def check_folder_status(self):
        """Check the status of the cache folders.

        This includes registering existing ones and creating new ones if needed.
        """
        if self.last_lib_path != self.lib.library_dir:
            self.register_existing_folders()

        def create_folder() -> Path:
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
        if self.folder_dict:
            last_folder = sorted(self.folder_dict.keys())[-1]

            if self.folder_dict[last_folder] > CacheManager.FOLDER_SIZE:
                new_folder = create_folder()
                self.folder_dict[new_folder] = 0
        else:
            new_folder = create_folder()
            self.folder_dict[new_folder] = 0

    def get_current_folder(self) -> Path:
        """Get the current cache folder path that should be used."""
        self.check_folder_status()
        self.cull_folders()

        return sorted(self.folder_dict.keys())[-1]

    def register_existing_folders(self):
        """Scan and register any pre-existing cache folders with the most recent size."""
        self.last_lib_path = self.lib.library_dir
        self.folder_dict.clear()

        if self.last_lib_path:
            # Ensure thumbnail cache path exists.
            self.cache_dir().mkdir(exist_ok=True)
            # Registers any existing folders and counts the capacity of the most recent one.
            for f in sorted(self.cache_dir().glob("*")):
                if f.is_dir():
                    # A folder is found. Add it to the class dict.BlockingIOError
                    self.folder_dict[f] = 0
            self.folder_dict = dict(sorted(self.folder_dict.items(), key=lambda kv: kv[0]))

            if self.folder_dict:
                last_folder = sorted(self.folder_dict.keys())[-1]
                for f in last_folder.glob("*"):
                    if not f.is_dir():
                        self.folder_dict[last_folder] += f.stat().st_size

            self.is_init = True

    def cull_folders(self):
        """Remove folders and their cached context based on size or age limits."""
        if len(self.folder_dict) > (self.size_limit / CacheManager.FOLDER_SIZE):
            f = sorted(self.folder_dict.keys())[0]
            folder = self.cache_dir() / f
            logger.info("[CacheManager] Removing folder due to size limit", folder=folder)

            for file in folder.glob("*"):
                with contextlib.suppress(FileNotFoundError):
                    file.unlink()
            try:
                folder.rmdir()
                with contextlib.suppress(KeyError):
                    self.folder_dict.pop(f)
                self.cull_folders()
            except FileNotFoundError:
                pass
