# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import math
from datetime import datetime as dt
from pathlib import Path
from threading import RLock

import structlog
from PIL import Image

from tagstudio.core.constants import THUMB_CACHE_NAME, TS_FOLDER_NAME

logger = structlog.get_logger(__name__)


class CacheManager:
    DEFAULT_MAX_SIZE = 500_000_000
    DEFAULT_MAX_FOLDER_SIZE = 10_000_000

    def __init__(
        self,
        library_dir: Path,
        max_size: int = DEFAULT_MAX_SIZE,
        max_folder_size: int = DEFAULT_MAX_FOLDER_SIZE,
    ):
        self._lock = RLock()
        self.cache_folder = library_dir / TS_FOLDER_NAME / THUMB_CACHE_NAME
        self.max_folder_size = max_folder_size
        self.max_size = max(max_size, max_folder_size)

        self.folders: dict[Path, int] = {}
        self.current_size = 0
        if self.cache_folder.exists():
            for folder in self.cache_folder.iterdir():
                if not folder.is_dir():
                    continue
                folder_size = 0
                for file in folder.iterdir():
                    folder_size += file.stat().st_size
                self.folders[folder] = folder_size
                self.current_size += folder_size

    def clear_cache(self):
        """Clear all files and folders within the cached folder."""
        with self._lock as _lock:
            folders = list(self.folders.keys())
            for folder in folders:
                if not self._remove_folder(folder):
                    logger.warn("[CacheManager] Failed to remove folder", folder=folder)
        logger.info("[CacheManager] Cleared cache!")

    def _remove_folder(self, folder: Path) -> bool:
        with self._lock as _lock:
            if folder not in self.folders:
                return False
            size = self.folders.pop(folder)
            self.current_size -= size
            if not folder.is_dir():
                return False

            is_empty = True
            for file in folder.iterdir():
                assert file.is_file() and file.suffix == ".webp"
                try:
                    file.unlink(missing_ok=True)
                except BaseException as e:
                    is_empty = False
                    logger.warn("[CacheManager] Failed to remove file", file=file, error=e)

            if is_empty:
                folder.rmdir()
                return True
            else:
                size = 0
                for file in folder.iterdir():
                    size += file.stat().st_size
                self.folders[folder] = size
                self.current_size += size
            return False

    def get_file_path(self, file_name: Path) -> Path | None:
        with self._lock as _lock:
            for folder in sorted(self.folders.keys()):
                file_path = folder / file_name
                if file_path.exists():
                    return file_path
        return None

    def save_image(self, image: Image.Image, file_name: Path, mode: str = "RGBA"):
        """Save an image to the cache."""
        with self._lock as _lock:
            folder = self._get_current_folder()
            file_path = folder / file_name
            image.save(file_path, mode=mode)

            size = file_path.stat().st_size
            self.folders[folder] += size
            self.current_size += size
            self._cull_folders()

    def _create_folder(self) -> Path:
        with self._lock as _lock:
            folder = self.cache_folder / Path(str(math.floor(dt.timestamp(dt.now()))))
            try:
                folder.mkdir(parents=True)
            except FileExistsError:
                return folder
            self.folders[folder] = 0
            return folder

    def _get_current_folder(self) -> Path:
        with self._lock as _lock:
            if len(self.folders) == 0:
                return self._create_folder()
            folders = sorted(self.folders.keys())
            if self.folders[folders[-1]] >= self.max_folder_size:
                return self._create_folder()

            folder = folders[-1]
            if not folder.is_dir():
                logger.warn("[CacheManager] Invalid folder", folder=folder)
                self._remove_folder(folder)
                return self._create_folder()
            return folder

    def _cull_folders(self):
        """Remove folders and their cached context based on size or age limits."""
        with self._lock as _lock:
            if self.current_size < self.max_size:
                return

            folders = sorted(self.folders.keys(), reverse=True)
            while self.current_size >= self.max_size:
                folder = folders.pop(-1)
                logger.info("[CacheManager] Removing folder due to size limit", folder=folder)
                self._remove_folder(folder)
