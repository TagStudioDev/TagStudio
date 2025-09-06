# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import math
from collections.abc import Iterable
from datetime import datetime as dt
from pathlib import Path
from threading import RLock

import structlog
from PIL import Image

from tagstudio.core.constants import THUMB_CACHE_NAME, TS_FOLDER_NAME
from tagstudio.qt.global_settings import DEFAULT_CACHED_IMAGE_QUALITY, DEFAULT_THUMB_CACHE_SIZE

logger = structlog.get_logger(__name__)


class CacheFolder:
    def __init__(self, path: Path, size: int):
        self.path: Path = path
        self.size: int = size


class CacheManager:
    MAX_FOLDER_SIZE = 10  # Absolute maximum size of a folder, number in MiB
    STAT_MULTIPLIER = 1_000_000  # Multiplier to apply to file stats (bytes) to get user units (MiB)

    def __init__(
        self,
        library_dir: Path,
        max_size: int | float = DEFAULT_THUMB_CACHE_SIZE,
        img_quality: int = DEFAULT_CACHED_IMAGE_QUALITY,
    ):
        """A class for managing frontend caches, such as for file thumbnails.

        Args:
            library_dir(Path): The path of the folder containing the .TagStudio library folder.
            max_size: (int | float) The maximum size of the cache, in MiB.
            img_quality: (int) The image quality value to save PIL images (0-100, default=80)
        """
        self._lock = RLock()
        self.cache_path = library_dir / TS_FOLDER_NAME / THUMB_CACHE_NAME
        self.max_size: int = max(
            math.floor(max_size * CacheManager.STAT_MULTIPLIER),
            math.floor(CacheManager.MAX_FOLDER_SIZE * CacheManager.STAT_MULTIPLIER),
        )
        self.img_quality = (
            img_quality if img_quality >= 0 and img_quality <= 100 else DEFAULT_CACHED_IMAGE_QUALITY
        )

        self.folders: list[CacheFolder] = []
        self.current_size = 0
        if self.cache_path.exists():
            for folder in self.cache_path.iterdir():
                if not folder.is_dir():
                    continue
                folder_size = 0
                for file in folder.iterdir():
                    folder_size += file.stat().st_size
                self.folders.append(CacheFolder(folder, folder_size))
                self.current_size += folder_size

    def _set_most_recent_folder(self, index: int):
        """Move CacheFolder at index so it's considered the most recently used folder."""
        with self._lock as _lock:
            if index == (len(self.folders) - 1):
                return
            cache_folder = self.folders.pop(index)
            self.folders.append(cache_folder)

    def _get_most_recent_folder(self) -> Iterable[int]:
        """Get each folders index sorted most recently used first."""
        with self._lock as _lock:
            return reversed(range(len(self.folders)))

    def _least_recent_folder(self) -> Iterable[int]:
        """Get each folder's index sorted least recently used first."""
        with self._lock as _lock:
            return range(len(self.folders))

    def clear_cache(self):
        """Clear all files and folders within the cached folder."""
        with self._lock as _lock:
            folders = []
            for folder in self.folders:
                if not self._remove_folder(folder):
                    folders.append(folders)
                    logger.warn("[CacheManager] Failed to remove folder", folder=folder)
            self.folders = folders
        logger.info("[CacheManager] Cleared cache!")

    def _remove_folder(self, cache_folder: CacheFolder) -> bool:
        with self._lock as _lock:
            self.current_size -= cache_folder.size
            if not cache_folder.path.is_dir():
                return True

            is_empty = True
            for file in cache_folder.path.iterdir():
                assert file.is_file() and file.suffix == ".webp"
                try:
                    file.unlink(missing_ok=True)
                except BaseException as e:
                    is_empty = False
                    logger.warn("[CacheManager] Failed to remove file", file=file, error=e)

            if is_empty:
                cache_folder.path.rmdir()
                return True
            else:
                size = 0
                for file in cache_folder.path.iterdir():
                    size += file.stat().st_size
                cache_folder.size = size
                self.current_size += size
            return False

    def get_file_path(self, file_name: Path) -> Path | None:
        with self._lock as _lock:
            for i in self._get_most_recent_folder():
                cache_folder = self.folders[i]
                file_path = cache_folder.path / file_name
                if file_path.exists():
                    self._set_most_recent_folder(i)
                    return file_path
        return None

    def save_image(self, image: Image.Image, file_name: Path, mode: str = "RGBA"):
        """Save an image to the cache."""
        with self._lock as _lock:
            cache_folder: CacheFolder = self._get_current_folder()
            file_path = cache_folder.path / file_name
            try:
                image.save(file_path, mode=mode, quality=self.img_quality)

                size = file_path.stat().st_size
                cache_folder.size += size
                self.current_size += size
                self._cull_folders()
            except FileNotFoundError:
                logger.warn(
                    "[CacheManager] Failed to save cached image, was the folder deleted on disk?",
                    folder=file_path,
                )
                if not cache_folder.path.exists():
                    self.folders.remove(cache_folder)

    def _create_folder(self) -> CacheFolder:
        with self._lock as _lock:
            folder = self.cache_path / Path(str(math.floor(dt.timestamp(dt.now()))))
            try:
                folder.mkdir(parents=True)
            except FileExistsError:
                for cache_folder in self.folders:
                    if cache_folder.path == folder:
                        return cache_folder
            cache_folder = CacheFolder(folder, 0)
            self.folders.append(cache_folder)
            return cache_folder

    def _get_current_folder(self) -> CacheFolder:
        with self._lock as _lock:
            if len(self.folders) == 0:
                return self._create_folder()

            for i in self._get_most_recent_folder():
                cache_folder: CacheFolder = self.folders[i]
                if cache_folder.size < CacheManager.MAX_FOLDER_SIZE * CacheManager.STAT_MULTIPLIER:
                    self._set_most_recent_folder(i)
                    return cache_folder

            return self._create_folder()

    def _cull_folders(self):
        """Remove folders and their cached context based on size or age limits."""
        with self._lock as _lock:
            if self.current_size < self.max_size:
                return

            removed: list[int] = []
            for i in self._least_recent_folder():
                cache_folder: CacheFolder = self.folders[i]
                logger.info(
                    "[CacheManager] Removing folder due to size limit", folder=cache_folder.path
                )
                if self._remove_folder(cache_folder):
                    removed.append(i)
                if self.current_size < self.max_size:
                    break

            for index in sorted(removed, reverse=True):
                self.folders.pop(index)
