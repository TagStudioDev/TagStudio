# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from pathlib import Path

from PIL import ImageQt
from PySide6.QtCore import QObject, QSize, Signal
from PySide6.QtGui import QGuiApplication, QPixmap, Qt

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.cache_manager import CacheManager
from tagstudio.qt.global_settings import GlobalSettings, Theme
from tagstudio.qt.previews.renderer import FileRenderer


class QtFileRenderer(QObject):
    updated = Signal(float, QPixmap, QSize, Path)
    updated_ratio = Signal(float)

    """A Qt-specific entry point for rendering file previews and thumbnails."""

    def __init__(self, library: Library, settings: GlobalSettings) -> None:
        super().__init__()
        self.renderer = FileRenderer(library, settings)
        self.theme = (
            Theme.DARK
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.LIGHT
        )

    def render(
        self,
        cache: CacheManager | None,
        timestamp: float,
        filepath: Path | str,
        base_size: tuple[int, int],
        pixel_ratio: float,
        is_loading: bool = False,
        is_grid_thumb: bool = False,
    ):

        image, size, timestamp = self.renderer.render(
            cache=cache,
            timestamp=timestamp,
            filepath=filepath,
            base_size=base_size,
            pixel_ratio=pixel_ratio,
            theme=self.theme,
            is_loading=is_loading,
            is_grid_thumb=is_grid_thumb,
        )
        qim = ImageQt.ImageQt(image)
        pixmap = QPixmap.fromImage(qim)
        pixmap.setDevicePixelRatio(pixel_ratio)

        self.updated_ratio.emit(image.size[0] / image.size[1])
        if pixmap:
            self.updated.emit(timestamp, pixmap, QSize(size[0], size[1]), filepath)
        else:
            self.updated.emit(timestamp, QPixmap(), QSize(*base_size), filepath)
