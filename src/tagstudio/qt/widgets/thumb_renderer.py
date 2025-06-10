# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import enum
import math
import time
from collections.abc import Callable, Iterable
from concurrent.futures import Future
from pathlib import Path
from typing import Any

import structlog
from PIL import (
    Image,
    ImageQt,
)
from PySide6.QtCore import (
    QObject,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QGuiApplication, QPixmap

from tagstudio.core.constants import (
    THUMB_CACHE_NAME,
    TS_FOLDER_NAME,
)
from tagstudio.core.palette import UiColor
from tagstudio.qt.render import (
    _get_resource_id,
    _render_icon,
    _render_preview,
    _render_thumbnail,
    init_pool,
)
from tagstudio.qt.resource_manager import ResourceManager

logger = structlog.get_logger(__name__)


class RenderJob(QObject):
    updated = Signal(float, QPixmap, QSize, Path)
    updated_ratio = Signal(float, float)

    def on_finish(
        self,
        timestamp: float,
        file_path: Path,
        base_size: tuple[int, int],
        pixel_ratio: float,
        image: Image.Image | None,
    ):
        if image is None:
            pixmap = QPixmap()
            qsize = QSize(*base_size)
            ratio = 1.0
        else:
            adj_size = math.ceil(max(base_size[0], base_size[1]) * pixel_ratio)
            qim = ImageQt.ImageQt(image)
            pixmap = QPixmap.fromImage(qim)
            pixmap.setDevicePixelRatio(pixel_ratio)
            qsize = QSize(
                math.ceil(adj_size / pixel_ratio),
                math.ceil(image.size[1] / pixel_ratio),
            )
            ratio = image.size[0] / image.size[1]

        self.updated.emit(
            timestamp,
            pixmap,
            qsize,
            file_path,
        )
        self.updated_ratio.emit(timestamp, ratio)


class JobType(enum.Enum):
    Icon = 0
    Preview = 1
    Thumbnail = 2


# fn(timestamp, file_path, base_size, pixel_ratio, image) -> Any
Callback = Callable[[float, Path, tuple[int, int], float, Image.Image | None], Any]


class ThumbnailManager:
    def __init__(self, library_path: Path) -> None:
        self.cache_folder = library_path / TS_FOLDER_NAME / THUMB_CACHE_NAME
        self.rm = ResourceManager()

        self._pool = init_pool()
        self._jobs: dict[tuple[JobType, Path], Future[Image.Image | None]] = {}
        self._callbacks: dict[tuple[JobType, Path], list[tuple[float, Callback]]] = {}
        self._error_cache: dict[tuple[JobType, Path], Future[Image.Image | None]] = {}

    def close(self):
        self._pool.shutdown(cancel_futures=True)
        self._jobs.clear()
        self._callbacks.clear()
        self._error_cache.clear()

    def cancel_pending_thumbnails(self):
        thumbnail_jobs = []
        for job_type, file_path in self._jobs:
            if job_type == JobType.Thumbnail:
                thumbnail_jobs.append((job_type, file_path))
        for key in thumbnail_jobs:
            job = self._jobs.pop(key)
            job.cancel()

    def render_thumbnail(
        self,
        file_path: Path,
        base_size: tuple[int, int],
        pixel_ratio: float,
        callback: Callback | None,
    ):
        is_dark_theme = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        key = (JobType.Thumbnail, file_path)
        fn = _render_thumbnail
        args = (file_path, base_size, pixel_ratio, is_dark_theme, self.cache_folder)
        self._queue_job(key, base_size, pixel_ratio, fn, args, callback)

    def render_preview(
        self,
        file_path: Path,
        base_size: tuple[int, int],
        pixel_ratio: float,
        callback: Callback | None,
    ):
        is_dark_theme = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        key = (JobType.Preview, file_path)
        fn = _render_preview
        args = (file_path, base_size, pixel_ratio, is_dark_theme)
        self._queue_job(key, base_size, pixel_ratio, fn, args, callback)

    def render_icon(
        self,
        file_path: Path,
        base_size: tuple[int, int],
        pixel_ratio: float,
        color: UiColor,
        draw_border: bool,
        callback: Callback | None,
    ):
        is_dark_theme = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        key = (JobType.Icon, file_path)
        fn = _render_icon
        args = (file_path, color, base_size, pixel_ratio, draw_border, is_dark_theme)
        self._queue_job(key, base_size, pixel_ratio, fn, args, callback)

    def _queue_job(
        self,
        key: tuple[JobType, Path],
        base_size: tuple[int, int],
        pixel_ratio: float,
        fn: Callable,
        args: Iterable[Any],
        callback: Callback | None,
    ):
        timestamp = time.time()
        if key in self._jobs:
            if callback is not None:
                self._callbacks.setdefault(key, []).append((timestamp, callback))
            return

        if key in self._error_cache:
            job = self._error_cache[key]
        else:
            job = self._pool.submit(fn, *args)
            self._jobs[key] = job

        if callback is not None:
            self._callbacks[key] = [(timestamp, callback)]
        job.add_done_callback(lambda job: self._on_completed(key, base_size, pixel_ratio, job))

    def _on_completed(
        self,
        key: tuple[JobType, Path],
        base_size: tuple[int, int],
        pixel_ratio: float,
        job: Future[Image.Image | None],
    ):
        if key in self._jobs:
            self._jobs.pop(key)
        if key not in self._callbacks:
            return
        callbacks = self._callbacks.pop(key)
        if job.cancelled():
            return

        if error := job.exception():
            # Render unlinked
            if isinstance(error, FileNotFoundError):
                icon_path = self.rm.get_path("broken_link_icon")
                assert icon_path
                new_key = (JobType.Icon, icon_path)
                if key == new_key:
                    return

                color = UiColor.RED
                self.render_icon(
                    icon_path, base_size, pixel_ratio, color, draw_border=True, callback=None
                )
                o_callbacks = (
                    (ts, lambda t, _p, s, r, i, cb=cb: cb(t, key[1], s, r, i))
                    for ts, cb in callbacks
                )
                self._callbacks.setdefault(new_key, []).extend(o_callbacks)
            else:
                logger.error(
                    "[ThumbnailManager] Job error",
                    file_path=key[1],
                    error_name=type(error).__name__,
                    error=error,
                )
                self._error_cache[key] = job
            return

        image = job.result()
        if image is None:
            self._error_cache[key] = job
            # Render file_ext icon
            name = _get_resource_id(key[1])
            icon_path = self.rm.get_path(name)
            if icon_path is None:
                icon_path = self.rm.get_path("file_generic")
            assert icon_path
            new_key = (JobType.Icon, icon_path)
            if key == new_key:
                return

            theme_color = (
                UiColor.THEME_LIGHT
                if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Light
                else UiColor.THEME_DARK
            )
            self.render_icon(
                icon_path, base_size, pixel_ratio, theme_color, draw_border=True, callback=None
            )
            o_callbacks = (
                (ts, lambda t, _p, s, r, i, cb=cb: cb(t, key[1], s, r, i)) for ts, cb in callbacks
            )
            self._callbacks.setdefault(new_key, []).extend(o_callbacks)
            return

        for timestamp, callback in callbacks:
            try:
                callback(timestamp, key[1], base_size, pixel_ratio, image)
            except BaseException as e:
                logger.error(
                    "[ThumbnailManager] Callback error",
                    file_path=key[1],
                    error_name=type(e).__name__,
                    error=e,
                )
