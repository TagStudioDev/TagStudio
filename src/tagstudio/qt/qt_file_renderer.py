# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from pathlib import Path

from PIL import ImageQt
from PySide6.QtCore import QObject, QSize, Signal
from PySide6.QtGui import QGuiApplication, QPixmap, Qt

from tagstudio.core.library.alchemy.library import Library
from tagstudio.previews.renderer import FileRenderer
from tagstudio.qt.app_settings import AppSettings, Theme
from tagstudio.qt.cache_manager import CacheManager


class QtFileRenderer(QObject):
    """A Qt-specific wrapper for rendering image previews and thumbnails from files."""

    updated = Signal(float, QPixmap, QSize, Path)
    updated_ratio = Signal(float)

    def __init__(self, library: Library, settings: AppSettings) -> None:
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
        size: tuple[int, int],
        pixel_ratio: float,
        is_loading: bool = False,
        is_thumb: bool = False,
    ):

        image, size, timestamp = self.renderer.render(
            cache=cache,
            timestamp=timestamp,
            filepath=filepath,
            size=size,
            dpi_scale=pixel_ratio,
            theme=self.theme,
            is_loading=is_loading,
            is_thumb=is_thumb,
        )
        qim = ImageQt.ImageQt(image)
        pixmap = QPixmap.fromImage(qim)
        pixmap.setDevicePixelRatio(pixel_ratio)

        self.updated_ratio.emit(image.size[0] / image.size[1])
        if pixmap:
            self.updated.emit(timestamp, pixmap, QSize(size[0], size[1]), filepath)
        else:
            self.updated.emit(timestamp, QPixmap(), QSize(*size), filepath)
