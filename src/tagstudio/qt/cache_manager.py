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

logger = structlog.get_logger(__name__)


class CacheEntry:
    def __init__(self, path: Path, size: int):
        self.path: Path = path
        self.size: int = size


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

        self.folders: list[CacheEntry] = []
        self.current_size = 0
        if self.cache_folder.exists():
            for folder in self.cache_folder.iterdir():
                if not folder.is_dir():
                    continue
                folder_size = 0
                for file in folder.iterdir():
                    folder_size += file.stat().st_size
                self.folders.append(CacheEntry(folder, folder_size))
                self.current_size += folder_size

    def _set_mru(self, index: int):
        """Move entry at index so it's considered the most recently used."""
        with self._lock as _lock:
            if index == (len(self.folders) - 1):
                return
            entry = self.folders.pop(index)
            self.folders.append(entry)

    def _mru(self) -> Iterable[int]:
        """Get each folders index sorted most recently used first."""
        with self._lock as _lock:
            return reversed(range(len(self.folders)))

    def _lru(self) -> Iterable[int]:
        """Get each folders index sorted least recently used first."""
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

    def _remove_folder(self, entry: CacheEntry) -> bool:
        with self._lock as _lock:
            self.current_size -= entry.size
            if not entry.path.is_dir():
                return True

            is_empty = True
            for file in entry.path.iterdir():
                assert file.is_file() and file.suffix == ".webp"
                try:
                    file.unlink(missing_ok=True)
                except BaseException as e:
                    is_empty = False
                    logger.warn("[CacheManager] Failed to remove file", file=file, error=e)

            if is_empty:
                entry.path.rmdir()
                return True
            else:
                size = 0
                for file in entry.path.iterdir():
                    size += file.stat().st_size
                entry.size = size
                self.current_size += size
            return False

    def get_file_path(self, file_name: Path) -> Path | None:
        with self._lock as _lock:
            for i in self._mru():
                entry = self.folders[i]
                file_path = entry.path / file_name
                if file_path.exists():
                    self._set_mru(i)
                    return file_path
        return None

    def save_image(self, image: Image.Image, file_name: Path, mode: str = "RGBA"):
        """Save an image to the cache."""
        with self._lock as _lock:
            entry = self._get_current_folder()
            file_path = entry.path / file_name
            image.save(file_path, mode=mode)

            size = file_path.stat().st_size
            entry.size += size
            self.current_size += size
            self._cull_folders()

    def _create_folder(self) -> CacheEntry:
        with self._lock as _lock:
            folder = self.cache_folder / Path(str(math.floor(dt.timestamp(dt.now()))))
            try:
                folder.mkdir(parents=True)
            except FileExistsError:
                for entry in self.folders:
                    if entry.path == folder:
                        return entry
            entry = CacheEntry(folder, 0)
            self.folders.append(entry)
            return entry

    def _get_current_folder(self) -> CacheEntry:
        with self._lock as _lock:
            if len(self.folders) == 0:
                return self._create_folder()

            for i in self._mru():
                entry = self.folders[i]
                if entry.size < self.max_folder_size:
                    self._set_mru(i)
                    return entry

            return self._create_folder()

    def _cull_folders(self):
        """Remove folders and their cached context based on size or age limits."""
        with self._lock as _lock:
            if self.current_size < self.max_size:
                return

            removed: list[int] = []
            for i in self._lru():
                entry = self.folders[i]
                logger.info("[CacheManager] Removing folder due to size limit", folder=entry.path)
                if self._remove_folder(entry):
                    removed.append(i)
                if self.current_size < self.max_size:
                    break

            for index in sorted(removed, reverse=True):
                self.folders.pop(index)
