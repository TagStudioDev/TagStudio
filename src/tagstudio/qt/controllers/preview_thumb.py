# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import io
import math
import time
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, override

import cv2
import rawpy
import structlog
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import QBuffer, QByteArray, QSize, Signal
from PySide6.QtGui import QMovie, QPixmap, QResizeEvent
from PySide6.QtWidgets import QWidget
from rawpy import LibRawFileUnsupportedError, LibRawIOError  # pyright: ignore

from tagstudio.core.media_types import MediaTypes
from tagstudio.core.query_lang.file_groups import SEARCH
from tagstudio.previews.video_tester import is_readable_video
from tagstudio.qt.mixed.file_attributes import FileAttributeData
from tagstudio.qt.mixed.media_player import MediaPlayer
from tagstudio.qt.qt_file_renderer import QtFileRenderer
from tagstudio.qt.utils.file_opener import open_file
from tagstudio.qt.views.preview_thumb_view import PreviewThumbView
from tagstudio.qt.views.styles.rounded_pixmap_style import RoundedPixmapStyle

if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)
Image.MAX_IMAGE_PIXELS = None

_DEFAULT_PREVIEW_SIZE = (272, 272)
_THUMB_SIZE_FACTOR = 2


class _PreviewType(Enum):
    """Enum for which of the Inspector's stacked pages should be shown for a file."""

    ANIMATED = auto()
    AUDIO = auto()
    IMAGE = auto()
    TEXT = auto()
    VIDEO = auto()


class PreviewThumb(QWidget):
    """The file preview thumbnail widget."""

    check_ffmpeg = Signal(bool)
    stats_updated = Signal(Path, FileAttributeData)

    def __init__(self, driver: QtDriver):
        super().__init__()
        self._driver = driver
        self._thumb_renderer = QtFileRenderer(driver.lib, driver.settings)

        self._current_file: Path | None = None
        self._gif_buffer: QBuffer = QBuffer()
        self._image_ratio: float = 1.0
        self._preview_size: tuple[int, int] = _DEFAULT_PREVIEW_SIZE
        self._rendered_res: tuple[int, int] = (0, 0)
        self._should_render_on_resize: bool = False

        self.setMinimumSize(*self._preview_size)
        self.setLayout(PreviewThumbView(driver))
        self._connect_callbacks()

        self.hide_preview()

    @override
    def layout(self) -> PreviewThumbView:
        return super().layout()  # pyright: ignore[reportReturnType]

    def _connect_callbacks(self) -> None:
        view = self.layout()
        view.open_file_action.triggered.connect(self._open_file_action_callback)
        view.open_explorer_action.triggered.connect(self._open_explorer_action_callback)
        view.delete_action.triggered.connect(self._delete_action_callback)
        view.button_wrapper.clicked.connect(self._button_wrapper_callback)

        # QMediaPlayer loads duration asynchronously after setSource().
        view.media_player.player.durationChanged.connect(
            self._media_player_duration_changed_callback
        )
        # Need to watch for this to resize the player appropriately.
        view.media_player.player.hasVideoChanged.connect(self._media_player_video_changed_callback)

        self._thumb_renderer.updated.connect(self._thumb_renderer_updated_callback)
        self._thumb_renderer.updated_ratio.connect(self._thumb_renderer_updated_ratio_callback)

    def _open_file_action_callback(self) -> None:
        if self._current_file:
            open_file(
                self._current_file,
                windows_start_command=self._driver.settings.windows_start_command,
            )

    def _open_explorer_action_callback(self) -> None:
        if self._current_file:
            open_file(self._current_file, file_manager=True)

    def _delete_action_callback(self) -> None:
        if self._current_file:
            self._driver.delete_files_callback(self._current_file)

    def _button_wrapper_callback(self) -> None:
        if self._current_file:
            open_file(
                self._current_file,
                windows_start_command=self._driver.settings.windows_start_command,
            )

    def _media_player_video_changed_callback(self) -> None:
        self._update_image_size((self.size().width(), self.size().height()))

    def _media_player_duration_changed_callback(self, duration_ms: int) -> None:
        filepath = self.layout().media_player.filepath
        if filepath is None or duration_ms <= 0:
            return

        self.stats_updated.emit(
            filepath,
            FileAttributeData(duration=duration_ms // 1000),
        )

    def _thumb_renderer_updated_callback(
        self, _timestamp: float, img: QPixmap, _size: QSize, _path: Path
    ) -> None:
        self.layout().button_wrapper.setIcon(img)

    def _thumb_renderer_updated_ratio_callback(self, ratio: float) -> None:
        self._image_ratio = ratio
        self._update_image_size((self.size().width(), self.size().height()))

    def _update_image_size(self, size: tuple[int, int]) -> None:
        view = self.layout()
        adj_width: float = size[0]
        adj_height: float = size[1]
        # Landscape
        if self._image_ratio > 1:
            adj_height = size[0] * (1 / self._image_ratio)
        # Portrait
        elif self._image_ratio <= 1:
            adj_width = size[1] * self._image_ratio

        if adj_width > size[0]:
            adj_height = adj_height * (size[0] / adj_width)
            adj_width = size[0]
        elif adj_height > size[1]:
            adj_width = adj_width * (size[1] / adj_height)
            adj_height = size[1]

        adj_size = QSize(int(adj_width), int(adj_height))

        self._preview_size = (int(adj_width), int(adj_height))
        view.button_wrapper.setMaximumSize(adj_size)
        view.button_wrapper.setIconSize(adj_size)
        view.preview_gif.setMaximumSize(adj_size)
        view.preview_gif.setMinimumSize(adj_size)

        view.media_player.setMaximumSize(adj_size)
        view.media_player.setMinimumSize(adj_size)

        proxy_style = RoundedPixmapStyle(radius=8)
        view.preview_gif.setStyle(proxy_style)
        view.media_player.setStyle(proxy_style)
        m = view.preview_gif.movie()
        if m:
            m.setScaledSize(adj_size)

    def _switch_preview(self, preview: _PreviewType | None) -> None:
        view = self.layout()
        if preview in [_PreviewType.AUDIO, _PreviewType.VIDEO]:
            view.media_player.show()
            view.setCurrentWidget(view.media_player_page)
            view.media_player_page.raise_()
            self.check_ffmpeg.emit(True)  # noqa: FBT003
        else:
            view.media_player.stop()
            view.media_player.hide()
            self.check_ffmpeg.emit(False)  # noqa: FBT003

        if preview in [_PreviewType.IMAGE, _PreviewType.AUDIO]:
            view.button_wrapper.show()
            current_page = (
                view.preview_img_page if preview == _PreviewType.IMAGE else view.media_player_page
            )
            view.setCurrentWidget(current_page)
            current_page.raise_()
        else:
            view.button_wrapper.hide()

        if preview == _PreviewType.ANIMATED:
            view.preview_gif.show()
            view.setCurrentWidget(view.preview_gif_page)
            view.preview_gif_page.raise_()
        else:
            if view.preview_gif.movie():
                view.preview_gif.movie().stop()
                self._gif_buffer.close()
            view.preview_gif.hide()

    def _render_thumb(self, filepath: Path) -> None:
        self._should_render_on_resize = True

        self._rendered_res = (
            math.ceil(self._preview_size[0] * _THUMB_SIZE_FACTOR),
            math.ceil(self._preview_size[1] * _THUMB_SIZE_FACTOR),
        )

        # TODO: Make driver update the cache manager reference here instead of passing the driver.
        self._thumb_renderer.render(
            self._driver.cache_manager,
            time.time(),
            filepath,
            self._rendered_res,
            self.devicePixelRatio(),
        )

    def _update_media_player(self, filepath: Path) -> None:
        """Display either audio or video."""
        self.layout().media_player.play(filepath)

    def _display_video(self, filepath: Path, size: QSize | None) -> FileAttributeData:
        self._should_render_on_resize = False

        self._switch_preview(_PreviewType.VIDEO)
        self._update_media_player(filepath)
        stats = FileAttributeData()

        if size is not None:
            stats.width = size.width()
            stats.height = size.height()

            self._image_ratio = stats.width / stats.height
            self.resizeEvent(
                QResizeEvent(
                    QSize(stats.width, stats.height),
                    QSize(stats.width, stats.height),
                )
            )

        return stats

    def _display_audio(self, filepath: Path) -> FileAttributeData:
        self._switch_preview(_PreviewType.AUDIO)
        self._render_thumb(filepath)
        self._update_media_player(filepath)
        return FileAttributeData()

    def _display_gif(self, gif_data: bytes, size: tuple[int, int]) -> FileAttributeData | None:
        """Update the animated image preview from a filepath."""
        self._should_render_on_resize = False

        view = self.layout()
        stats = FileAttributeData()

        # Ensure that any movie and buffer from previous animations are cleared.
        if view.preview_gif.movie():
            view.preview_gif.movie().stop()
            self._gif_buffer.close()

        stats.width = size[0]
        stats.height = size[1]

        self._image_ratio = stats.width / stats.height

        self._gif_buffer.setData(gif_data)
        movie = QMovie(self._gif_buffer, QByteArray())
        view.preview_gif.setMovie(movie)

        # If the animation only has 1 frame, it isn't animated and shouldn't be treated as such
        if movie.frameCount() <= 1:
            return None

        # The animation has more than 1 frame, continue displaying it as an animation
        self._switch_preview(_PreviewType.ANIMATED)
        self.resizeEvent(
            QResizeEvent(
                QSize(stats.width, stats.height),
                QSize(stats.width, stats.height),
            )
        )
        movie.start()
        stats.duration = movie.frameCount() // 60

        return stats

    def _display_image(self, filepath: Path):
        """Renders the given file as an image, no matter its media type."""
        self._switch_preview(_PreviewType.IMAGE)
        self._render_thumb(filepath)

    def hide_preview(self) -> None:
        """Completely hide the file preview."""
        self._switch_preview(None)
        self._current_file = None
        self._should_render_on_resize = False

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self._update_image_size((self.size().width(), self.size().height()))

        if (
            self._current_file is not None
            and self._should_render_on_resize
            and self._rendered_res < self._preview_size
        ):
            self._render_thumb(self._current_file)

        return super().resizeEvent(event)

    @property
    def media_player(self) -> MediaPlayer:
        return self.layout().media_player

    @property
    def current_file(self) -> Path | None:
        return self._current_file

    def _get_image_stats(self, filepath: Path) -> FileAttributeData:
        """Get width and height of an image as dict."""
        stats = FileAttributeData()
        ext = filepath.suffix.lower()

        if filepath.is_dir():
            pass
        elif MediaTypes.contains("image.raster.raw", ext, SEARCH):
            try:
                with rawpy.imread(str(filepath)) as raw:
                    rgb = raw.postprocess()
                    image = Image.new("L", (rgb.shape[1], rgb.shape[0]), color="black")
                    stats.width = image.width
                    stats.height = image.height
            except (
                LibRawIOError,
                LibRawFileUnsupportedError,
                FileNotFoundError,
            ):
                pass
        elif MediaTypes.contains("image.raster", ext, SEARCH):
            try:
                image = Image.open(str(filepath))
                stats.width = image.width
                stats.height = image.height
            except (
                DecompressionBombError,
                FileNotFoundError,
                NotImplementedError,
                UnidentifiedImageError,
            ) as e:
                logger.error("[PreviewThumb] Could not get image stats", filepath=filepath, error=e)
        elif MediaTypes.contains("image.vector", ext, SEARCH):
            pass  # TODO

        return stats

    def _get_gif_data(self, filepath: Path) -> tuple[bytes, tuple[int, int]] | None:
        """Loads an animated image and returns gif data and size, if successful."""
        ext = filepath.suffix.lower()

        try:
            image: Image.Image = Image.open(filepath)
            if ext == ".apng":
                image_bytes_io = io.BytesIO()
                image.save(
                    image_bytes_io,
                    "GIF",
                    lossless=True,
                    save_all=True,
                    loop=0,
                    disposal=2,
                )
                image.close()
                image_bytes_io.seek(0)
                return (image_bytes_io.read(), (image.width, image.height))
            else:
                image.close()
                with open(filepath, "rb") as f:
                    return (f.read(), (image.width, image.height))

        except (UnidentifiedImageError, FileNotFoundError) as e:
            logger.error("[PreviewThumb] Could not load animated image", filepath=filepath, error=e)
            return None

    def _get_video_res(self, filepath: str) -> tuple[bool, QSize]:
        video = cv2.VideoCapture(filepath, cv2.CAP_FFMPEG)
        success, frame = video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        return (success, QSize(image.width, image.height))

    def display_file(self, filepath: Path) -> FileAttributeData:
        """Render a single file preview."""
        self._current_file = filepath
        ext = filepath.suffix.lower()

        # Video
        if MediaTypes.contains("video", ext, SEARCH) and is_readable_video(filepath):
            size: QSize | None = None
            try:
                success, size = self._get_video_res(str(filepath))
                if not success:
                    size = None
            except cv2.error as e:
                logger.error("[PreviewThumb] Could not play video", filepath=filepath, error=e)

            return self._display_video(filepath, size)
        # Audio
        elif MediaTypes.contains("audio", ext, SEARCH):
            return self._display_audio(filepath)
        # Animated Images
        elif MediaTypes.contains("image.animated", ext, SEARCH):
            if (ret := self._get_gif_data(filepath)) and (
                stats := self._display_gif(ret[0], ret[1])
            ) is not None:
                return stats
            else:
                self._display_image(filepath)
                return self._get_image_stats(filepath)
        # Other Types (Including Images)
        else:
            self._display_image(filepath)
            return self._get_image_stats(filepath)
