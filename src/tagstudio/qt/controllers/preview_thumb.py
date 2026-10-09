# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import io
import math
import time
from enum import Enum, auto
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, override

import rawpy
import structlog
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import QBuffer, QByteArray, QRectF, QSize, Qt, QThreadPool, Signal
from PySide6.QtGui import QBrush, QMovie, QPainter, QPixmap, QResizeEvent
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import QWidget
from rawpy import LibRawFileUnsupportedError, LibRawIOError  # pyright: ignore

from tagstudio.core.media_types import MediaTypes
from tagstudio.core.query_lang.file_groups import SEARCH
from tagstudio.core.utils.decompression import decompressed
from tagstudio.core.utils.types import unwrap
from tagstudio.previews.media_probe import (
    get_duration,
    get_video_stream,
    has_audio_stream,
    is_readable_video,
)
from tagstudio.qt.mixed.file_attributes import FileAttributeData
from tagstudio.qt.mixed.media_player import MediaPlayer
from tagstudio.qt.qt_file_renderer import QtFileRenderer
from tagstudio.qt.utils.file_opener import open_file
from tagstudio.qt.views.preview_thumb_view import PreviewThumbView
from tagstudio.qt.views.styles.stylesheets import RADIUS

if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)
Image.MAX_IMAGE_PIXELS = None

_DEFAULT_PREVIEW_SIZE = (272, 272)
_THUMB_SIZE_FACTOR = 2


class _PreviewType(Enum):
    """Enum for which of the Inspector's stacked pages should be displayed for a file."""

    ANIMATED = auto()
    AUDIO = auto()
    IMAGE = auto()
    TEXT = auto()
    VIDEO = auto()


class PreviewThumb(QWidget):
    """The file preview thumbnail widget."""

    _animation_loaded = Signal(Path, object)
    _video_probed = Signal(Path, object, object)
    check_ffmpeg = Signal(bool)
    stats_updated = Signal(Path, FileAttributeData)

    def __init__(self, driver: QtDriver):
        super().__init__()
        self._driver = driver
        self._file_renderer = QtFileRenderer(driver.lib, driver.settings)
        self._render_pool = QThreadPool(self)
        self._render_pool.setMaxThreadCount(1)

        self._animation_buffer: QBuffer = QBuffer()
        self._animation_size: QSize = QSize()
        self._current_file: Path | None = None
        self._date_modified: float | None = None
        self._image_ratio: float = 1.0
        self._preview_size: tuple[int, int] = _DEFAULT_PREVIEW_SIZE
        self._render_timestamp: float = 0.0
        self._rendered_res: tuple[int, int] = (0, 0)
        self._should_render_on_resize: bool = False
        self._source_pixmap: QPixmap = QPixmap()

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

        view.media_player.player.errorOccurred.connect(self._media_player_error_callback)
        # Need to watch for this to resize the player appropriately.
        view.media_player.player.hasVideoChanged.connect(self._media_player_video_changed_callback)

        self._file_renderer.updated.connect(self._file_renderer_updated_callback)
        self._animation_loaded.connect(self._animation_loaded_callback)
        self._video_probed.connect(self._video_probed_callback)

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

    def _media_player_error_callback(self, _error: QMediaPlayer.Error, _message: str) -> None:
        """Callback that fires when the media player encounters an error and can't play.

        Used to display a fallback image for videos if they can't play.
        """
        filepath = self.layout().media_player.filepath
        if (
            filepath is not None
            and filepath == self._current_file
            and MediaTypes.contains("video", filepath.suffix.lower(), SEARCH)
        ):
            self._display_image(filepath, is_new_file=True)

    def _video_probed_callback(
        self, filepath: Path, preview: _PreviewType | None, stats: FileAttributeData | None
    ) -> None:
        """Callback that fires once a video's probe results are back."""
        if filepath != self._current_file:
            return

        if preview == _PreviewType.VIDEO and stats is not None:
            # Display the video's size and duration
            if stats.width and stats.height:
                self._image_ratio = stats.width / stats.height
                self._update_image_size((self.size().width(), self.size().height()))
            self.stats_updated.emit(filepath, stats)
        elif preview == _PreviewType.AUDIO:
            # Display the album art/waveform and duration
            self._display_audio(filepath, is_new_file=True, start_player=False)
        else:
            self._display_image(filepath, is_new_file=True)

    def _animation_loaded_callback(
        self, filepath: Path, data: tuple[bytes, tuple[int, int]] | None
    ) -> None:
        if filepath != self._current_file:
            return

        if not (data and self._play_animation(*data)):
            self._display_image(filepath, is_new_file=False)

    def _file_renderer_updated_callback(
        self, timestamp: float, img: QPixmap, _size: QSize, path: Path
    ) -> None:
        if path != self._current_file or timestamp < self._render_timestamp:
            return

        self._source_pixmap = img
        self._image_ratio = img.width() / img.height()
        self._update_image_size((self.size().width(), self.size().height()), refresh_icon=True)

    def _update_icon(self) -> None:
        button = self.layout().button_wrapper
        if self._source_pixmap.isNull():
            button.setIcon(self._source_pixmap)
            return

        ratio = self.devicePixelRatio()
        scaled = self._source_pixmap.scaled(
            button.iconSize() * ratio,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        scaled.setDevicePixelRatio(1)
        pixmap = QPixmap(scaled.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(scaled))
        painter.drawRoundedRect(QRectF(pixmap.rect()), RADIUS * ratio, RADIUS * ratio)
        painter.end()
        pixmap.setDevicePixelRatio(ratio)
        button.setIcon(pixmap)

    def _update_image_size(self, size: tuple[int, int], refresh_icon: bool = False) -> None:
        view = self.layout()
        scaled_width: float = size[0]
        scaled_height: float = size[1]
        # Landscape
        if self._image_ratio > 1:
            scaled_height = size[0] * (1 / self._image_ratio)
        # Portrait
        elif self._image_ratio <= 1:
            scaled_width = size[1] * self._image_ratio

        if scaled_width > size[0]:
            scaled_height = scaled_height * (size[0] / scaled_width)
            scaled_width = size[0]
        elif scaled_height > size[1]:
            scaled_width = scaled_width * (size[1] / scaled_height)
            scaled_height = size[1]

        scaled_size = QSize(int(scaled_width), int(scaled_height))

        self._preview_size = (int(scaled_width), int(scaled_height))
        view.button_wrapper.setMaximumSize(scaled_size)
        view.button_wrapper.setMinimumSize(scaled_size)
        if refresh_icon or view.button_wrapper.iconSize() != scaled_size:
            view.button_wrapper.setIconSize(scaled_size)
            self._update_icon()
        view.preview_animation.setMaximumSize(scaled_size)
        view.preview_animation.setMinimumSize(scaled_size)

        view.media_player.setMaximumSize(scaled_size)
        view.media_player.setMinimumSize(scaled_size)

        for page in (view.preview_img_page, view.preview_animation_page, view.media_player_page):
            unwrap(page.layout()).activate()

        movie = view.preview_animation.movie()
        if movie:
            max_side = max(self._animation_size.width(), self._animation_size.height())
            display_max = max(scaled_size.width(), scaled_size.height()) * self.devicePixelRatio()
            is_upscaling = max_side < display_max
            movie.setScaledSize(QSize() if is_upscaling else scaled_size)

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
            view.preview_animation.show()
            view.setCurrentWidget(view.preview_animation_page)
            view.preview_animation_page.raise_()
        else:
            if view.preview_animation.movie():
                view.preview_animation.movie().stop()
                self._animation_buffer.close()
            view.preview_animation.hide()

    def _render_preview(self, filepath: Path) -> None:
        self._should_render_on_resize = True

        screen_size = self.screen().size()
        self._rendered_res = (
            min(math.ceil(self._preview_size[0] * _THUMB_SIZE_FACTOR), screen_size.width()),
            min(math.ceil(self._preview_size[1] * _THUMB_SIZE_FACTOR), screen_size.height()),
        )
        self._render_timestamp = time.time()

        # TODO: Make driver update the cache manager reference here instead of passing the driver.
        self._render_pool.start(
            partial(
                self._file_renderer.render,
                self._driver.cache_manager,
                self._render_timestamp,
                filepath,
                self._rendered_res,
                self.devicePixelRatio(),
                date_modified=self._date_modified,
            )
        )

    def _render_placeholder(self, filepath: Path) -> None:
        """Display the file's cached thumbnail, or a loading graphic if it has none.

        If a file is already known to not be renderable, it'll display the default icon for it
        right away instead of a loading graphic.
        Some filetypes shouldn't display a loading graphic ever, like fonts.
        """
        self._file_renderer.render(
            self._driver.cache_manager,
            time.time(),
            filepath,
            _DEFAULT_PREVIEW_SIZE,
            self.devicePixelRatio(),
            is_loading=True,
            date_modified=self._date_modified,
        )

    def _update_media_player(self, filepath: Path) -> None:
        """Display either audio or video."""
        self.layout().media_player.play(filepath)

    def _display_video(self, filepath: Path) -> None:
        """Play a video, loading its stats in the background."""
        self._should_render_on_resize = False

        self._switch_preview(_PreviewType.VIDEO)
        self._update_media_player(filepath)
        self._render_pool.start(lambda: self._probe_video(filepath))

    def _probe_video(self, filepath: Path) -> None:
        """Send whether a video should display as a video, as audio, or as an image."""
        if is_readable_video(filepath):
            self._video_probed.emit(filepath, _PreviewType.VIDEO, self._get_video_stats(filepath))
        elif has_audio_stream(filepath):
            self._video_probed.emit(filepath, _PreviewType.AUDIO, None)
        else:
            self._video_probed.emit(filepath, None, None)

    def _display_audio(self, filepath: Path, is_new_file: bool, start_player: bool = True) -> None:
        """Display an audio file's art and duration, and play it unless `start_player` is False."""
        self._render_pool.start(
            lambda: self.stats_updated.emit(filepath, self._get_duration_stats(filepath))
        )
        self._switch_preview(_PreviewType.AUDIO)
        if is_new_file:
            self._render_placeholder(filepath)
        self._render_preview(filepath)
        if start_player:
            self._update_media_player(filepath)

    def _play_animation(self, data: bytes, size: tuple[int, int]) -> bool:
        """Play an animated image, returning `False` if it's not actually animated."""
        self._should_render_on_resize = False

        view = self.layout()

        # Ensure that any movie and buffer from previous animations are cleared.
        if view.preview_animation.movie():
            view.preview_animation.movie().stop()
            self._animation_buffer.close()

        self._animation_size = QSize(*size)
        self._image_ratio = self._animation_size.width() / self._animation_size.height()

        self._animation_buffer.setData(data)
        movie = QMovie(self._animation_buffer, QByteArray())
        view.preview_animation.setMovie(movie)

        # If the animation only has 1 frame, it isn't animated and shouldn't be treated as such
        if movie.frameCount() <= 1:
            return False

        # The animation has more than 1 frame, continue displaying it as an animation
        self._switch_preview(_PreviewType.ANIMATED)
        self.resizeEvent(QResizeEvent(self._animation_size, self._animation_size))
        movie.start()
        return True

    def _display_animated_image(self, filepath: Path, is_new_file: bool) -> None:
        """Display a placeholder while the animation loads, falling back to a still image.

        The placeholder will be the cached first frame if it exists, or else a loading icon.
        """
        self._should_render_on_resize = False
        if is_new_file:
            self._switch_preview(_PreviewType.IMAGE)
            self._render_placeholder(filepath)
        self._render_pool.start(lambda: self._load_animation(filepath))

    def _load_animation(self, filepath: Path) -> None:
        """Send an animated image to be played, then its stats once its duration is known."""
        animation_data = self._get_animation_data(filepath)
        self._animation_loaded.emit(filepath, animation_data)
        if animation_data is not None:
            stats = self._get_duration_stats(filepath)
            stats.width, stats.height = animation_data[1]
            self.stats_updated.emit(filepath, stats)

    def _display_image(self, filepath: Path, is_new_file: bool) -> None:
        """Renders the given file as an image, no matter its media type."""
        self._switch_preview(_PreviewType.IMAGE)
        if is_new_file:
            self._render_placeholder(filepath)
        self._render_pool.start(
            lambda: self.stats_updated.emit(filepath, self._get_image_stats(filepath))
        )
        self._render_preview(filepath)

    def hide_preview(self) -> None:
        """Completely hide the file preview."""
        self._render_pool.clear()
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
            self._render_preview(self._current_file)

        return super().resizeEvent(event)

    @property
    def media_player(self) -> MediaPlayer:
        return self.layout().media_player

    @property
    def current_file(self) -> Path | None:
        return self._current_file

    def _get_image_stats(self, filepath: Path) -> FileAttributeData:
        """Get the width and height of an image."""
        stats = FileAttributeData()

        with decompressed(filepath) as image_path:
            if image_path is None:
                return stats
            ext = image_path.suffix.lower()

            if image_path.is_dir():
                pass
            elif MediaTypes.contains("image.raster.raw", ext, SEARCH):
                try:
                    with rawpy.imread(str(image_path)) as raw:
                        sizes = raw.sizes
                        is_rotated = bool(sizes.flip & 4)
                        stats.width = sizes.height if is_rotated else sizes.width
                        stats.height = sizes.width if is_rotated else sizes.height
                except (
                    LibRawIOError,
                    LibRawFileUnsupportedError,
                    FileNotFoundError,
                ):
                    pass
            elif MediaTypes.contains("image.raster", ext, SEARCH):
                try:
                    with Image.open(str(image_path)) as image:
                        stats.width = image.width
                        stats.height = image.height
                except (
                    DecompressionBombError,
                    FileNotFoundError,
                    NotImplementedError,
                    UnidentifiedImageError,
                ) as e:
                    logger.error(
                        "[PreviewThumb] Could not get image stats", filepath=filepath, error=e
                    )
            elif MediaTypes.contains("image.vector", ext, SEARCH):
                pass  # TODO

        return stats

    def _get_animation_data(self, filepath: Path) -> tuple[bytes, tuple[int, int]] | None:
        """Return an animated image's data and size, or `None` if it isn't animated."""
        ext = filepath.suffix.lower()

        try:
            with Image.open(filepath) as image:
                if not getattr(image, "is_animated", False):
                    return None

                size = (image.width, image.height)

                # QMovie can't play APNGs, so convert them to the fastest lossless WebP
                if ext == ".apng":
                    image_bytes_io = io.BytesIO()
                    image.save(
                        image_bytes_io,
                        "WEBP",
                        lossless=True,
                        quality=0,
                        method=0,
                        save_all=True,
                        loop=0,
                    )
                    return (image_bytes_io.getvalue(), size)

            with open(filepath, "rb") as f:
                return (f.read(), size)

        except (UnidentifiedImageError, FileNotFoundError) as e:
            logger.error("[PreviewThumb] Could not load animated image", filepath=filepath, error=e)
            return None

    def _get_duration_stats(self, filepath: Path) -> FileAttributeData:
        """Get the duration of a media file."""
        duration = get_duration(filepath)
        return FileAttributeData(duration=None if duration is None else int(duration))

    def _get_video_stats(self, filepath: Path) -> FileAttributeData:
        """Get a video's dimensions and duration."""
        stats = self._get_duration_stats(filepath)
        video = get_video_stream(filepath)
        if video and video.get("width") and video.get("height"):
            rotation = int(video.get("tags", {}).get("rotate", 0))
            for side_data in video.get("side_data_list", []):
                rotation = int(side_data.get("rotation", rotation))
            is_sideways = rotation % 180 != 0
            stats.width = video["height"] if is_sideways else video["width"]
            stats.height = video["width"] if is_sideways else video["height"]
        return stats

    def display_file(self, filepath: Path, date_modified: float | None = None) -> None:
        """Render a single file preview, sending its stats through `stats_updated`.

        `date_modified` is used to find unlinked files' cached thumbnails.
        """
        is_new_file = filepath != self._current_file
        self._current_file = filepath
        self._date_modified = date_modified
        self._render_pool.clear()
        ext = filepath.suffix.lower()

        # Video
        if MediaTypes.contains("video", ext, SEARCH):
            self._display_video(filepath)
        # Audio
        elif MediaTypes.contains("audio", ext, SEARCH):
            self._display_audio(filepath, is_new_file)
        # Animated Images
        elif MediaTypes.contains("image.animated", ext, SEARCH):
            self._display_animated_image(filepath, is_new_file)
        # Other Types (Including Images)
        else:
            self._display_image(filepath, is_new_file)
