# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import io
import time
from pathlib import Path
from typing import TYPE_CHECKING, override
from warnings import catch_warnings

import cv2
import rawpy
import structlog
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import QBuffer, QByteArray, QSize, Qt
from PySide6.QtGui import QAction, QMovie, QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QStackedLayout, QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaCategories, MediaType
from tagstudio.qt.helpers.file_opener import FileOpenerHelper, open_file
from tagstudio.qt.helpers.file_tester import is_readable_video
from tagstudio.qt.helpers.qbutton_wrapper import QPushButtonWrapper
from tagstudio.qt.helpers.rounded_pixmap_style import RoundedPixmapStyle
from tagstudio.qt.platform_strings import open_file_str, trash_term
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.media_player import MediaPlayer
from tagstudio.qt.widgets.thumb_renderer import ThumbRenderer

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)
Image.MAX_IMAGE_PIXELS = None


class PreviewThumb(QWidget):
    """The Preview Panel Widget."""

    def __init__(self, library: Library, driver: "QtDriver") -> None:
        super().__init__()

        self.is_connected = False
        self.lib = library
        self.driver: QtDriver = driver

        self.img_button_size: tuple[int, int] = (266, 266)
        self.image_ratio: float = 1.0

        self.image_layout = QStackedLayout(self)
        self.image_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.image_layout.setContentsMargins(0, 0, 0, 0)

        self.opener: FileOpenerHelper | None = None
        self.open_file_action = QAction(Translations["file.open_file"], self)
        self.open_explorer_action = QAction(open_file_str(), self)
        self.delete_action = QAction(
            Translations.format("trash.context.ambiguous", trash_term=trash_term()),
            self,
        )

        self.preview_img = QPushButtonWrapper()
        self.preview_img.setMinimumSize(*self.img_button_size)
        self.preview_img.setFlat(True)
        self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.preview_img.addAction(self.open_file_action)
        self.preview_img.addAction(self.open_explorer_action)
        self.preview_img.addAction(self.delete_action)

        # In testing, it didn't seem possible to center the widgets directly
        # on the QStackedLayout. Adding sublayouts allows us to center the widgets.
        self.preview_img_page = QWidget()
        self._stacked_page_setup(self.preview_img_page, self.preview_img)

        self.preview_gif = QLabel()
        self.preview_gif.setMinimumSize(*self.img_button_size)
        self.preview_gif.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.preview_gif.setCursor(Qt.CursorShape.ArrowCursor)
        self.preview_gif.addAction(self.open_file_action)
        self.preview_gif.addAction(self.open_explorer_action)
        self.preview_gif.addAction(self.delete_action)
        self.gif_buffer: QBuffer = QBuffer()

        self.preview_gif_page = QWidget()
        self._stacked_page_setup(self.preview_gif_page, self.preview_gif)

        self.media_player = MediaPlayer(driver)
        self.media_player.addAction(self.open_file_action)
        self.media_player.addAction(self.open_explorer_action)
        self.media_player.addAction(self.delete_action)

        # Need to watch for this to resize the player appropriately.
        self.media_player.player.hasVideoChanged.connect(self._has_video_changed)

        self.mp_max_size = QSize(*self.img_button_size)

        self.media_player_page = QWidget()
        self._stacked_page_setup(self.media_player_page, self.media_player)

        self.thumb_renderer = ThumbRenderer(self.lib)
        self.thumb_renderer.updated.connect(
            lambda ts, i, s: (
                self.preview_img.setIcon(i),
                self._set_mp_max_size(i.size()),
            )
        )
        self.thumb_renderer.updated_ratio.connect(
            lambda ratio: (
                self.set_image_ratio(ratio),
                self.update_image_size(
                    (
                        self.size().width(),
                        self.size().height(),
                    ),
                    ratio,
                ),
            )
        )

        self.image_layout.addWidget(self.preview_img_page)
        self.image_layout.addWidget(self.preview_gif_page)
        self.image_layout.addWidget(self.media_player_page)

        self.setMinimumSize(*self.img_button_size)

        self.hide_preview()

    def _set_mp_max_size(self, size: QSize) -> None:
        self.mp_max_size = size

    def _has_video_changed(self, video: bool) -> None:
        self.update_image_size((self.size().width(), self.size().height()))

    def _stacked_page_setup(self, page: QWidget, widget: QWidget) -> None:
        layout = QHBoxLayout(page)
        layout.addWidget(widget)
        layout.setAlignment(widget, Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        page.setLayout(layout)

    def set_image_ratio(self, ratio: float) -> None:
        self.image_ratio = ratio

    def update_image_size(self, size: tuple[int, int], ratio: float | None = None) -> None:
        if ratio:
            self.set_image_ratio(ratio)

        adj_width: float = size[0]
        adj_height: float = size[1]
        # Landscape
        if self.image_ratio > 1:
            adj_height = size[0] * (1 / self.image_ratio)
        # Portrait
        elif self.image_ratio <= 1:
            adj_width = size[1] * self.image_ratio

        if adj_width > size[0]:
            adj_height = adj_height * (size[0] / adj_width)
            adj_width = size[0]
        elif adj_height > size[1]:
            adj_width = adj_width * (size[1] / adj_height)
            adj_height = size[1]

        adj_size = QSize(int(adj_width), int(adj_height))

        self.img_button_size = (int(adj_width), int(adj_height))
        self.preview_img.setMaximumSize(adj_size)
        self.preview_img.setIconSize(adj_size)
        self.preview_gif.setMaximumSize(adj_size)
        self.preview_gif.setMinimumSize(adj_size)

        if not self.media_player.player.hasVideo():
            # ensure we do not exceed the thumbnail size
            mp_width = (
                adj_size.width()
                if adj_size.width() < self.mp_max_size.width()
                else self.mp_max_size.width()
            )
            mp_height = (
                adj_size.height()
                if adj_size.height() < self.mp_max_size.height()
                else self.mp_max_size.height()
            )
            mp_size = QSize(mp_width, mp_height)
            self.media_player.setMinimumSize(mp_size)
            self.media_player.setMaximumSize(mp_size)
        else:
            # have video, so just resize as normal
            self.media_player.setMaximumSize(adj_size)
            self.media_player.setMinimumSize(adj_size)

        proxy_style = RoundedPixmapStyle(radius=8)
        self.preview_gif.setStyle(proxy_style)
        self.media_player.setStyle(proxy_style)
        m = self.preview_gif.movie()
        if m:
            m.setScaledSize(adj_size)

    def get_preview_size(self) -> tuple[int, int]:
        return (
            self.size().width(),
            self.size().height(),
        )

    def switch_preview(self, preview: str) -> None:
        if preview in ["audio", "video"]:
            self.media_player.show()
            self.image_layout.setCurrentWidget(self.media_player_page)
        else:
            self.media_player.stop()
            self.media_player.hide()

        if preview in ["image", "audio"]:
            self.preview_img.show()
            self.image_layout.setCurrentWidget(
                self.preview_img_page if preview == "image" else self.media_player_page
            )
        else:
            self.preview_img.hide()

        if preview == "animated":
            self.preview_gif.show()
            self.image_layout.setCurrentWidget(self.preview_gif_page)
        else:
            if self.preview_gif.movie():
                self.preview_gif.movie().stop()
                self.gif_buffer.close()
            self.preview_gif.hide()

    def _display_fallback_image(self, filepath: Path, ext: str) -> dict[str, int]:
        """Renders the given file as an image, no matter its media type.

        Useful for fallback scenarios.
        """
        self.switch_preview("image")
        self.thumb_renderer.render(
            time.time(),
            filepath,
            (512, 512),
            self.devicePixelRatio(),
            update_on_ratio_change=True,
        )
        return self._update_image(filepath)

    def _update_image(self, filepath: Path) -> dict[str, int]:
        """Update the static image preview from a filepath."""
        stats: dict[str, int] = {}
        ext = filepath.suffix.lower()
        self.switch_preview("image")

        image: Image.Image | None = None

        if MediaCategories.is_ext_in_category(
            ext, MediaCategories.IMAGE_RAW_TYPES, mime_fallback=True
        ):
            try:
                with rawpy.imread(str(filepath)) as raw:
                    rgb = raw.postprocess()
                    image = Image.new("L", (rgb.shape[1], rgb.shape[0]), color="black")
                    stats["width"] = image.width
                    stats["height"] = image.height
            except (
                rawpy._rawpy._rawpy.LibRawIOError,  # pyright: ignore[reportAttributeAccessIssue]
                rawpy._rawpy.LibRawFileUnsupportedError,  # pyright: ignore[reportAttributeAccessIssue]
                FileNotFoundError,
            ):
                pass
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.IMAGE_RASTER_TYPES, mime_fallback=True
        ):
            try:
                image = Image.open(str(filepath))
                stats["width"] = image.width
                stats["height"] = image.height
            except (
                DecompressionBombError,
                FileNotFoundError,
                NotImplementedError,
                UnidentifiedImageError,
            ) as e:
                logger.error("[PreviewThumb] Could not get image stats", filepath=filepath, error=e)
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.IMAGE_VECTOR_TYPES, mime_fallback=True
        ):
            pass

        return stats

    def _update_animation(self, filepath: Path, ext: str) -> dict[str, int]:
        """Update the animated image preview from a filepath."""
        stats: dict[str, int] = {}

        # Ensure that any movie and buffer from previous animations are cleared.
        if self.preview_gif.movie():
            self.preview_gif.movie().stop()
            self.gif_buffer.close()

        try:
            image: Image.Image = Image.open(filepath)
            stats["width"] = image.width
            stats["height"] = image.height

            self.update_image_size((image.width, image.height), image.width / image.height)
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
                self.gif_buffer.setData(image_bytes_io.read())
            else:
                image.close()
                with open(filepath, "rb") as f:
                    self.gif_buffer.setData(f.read())
            movie = QMovie(self.gif_buffer, QByteArray())
            self.preview_gif.setMovie(movie)

            # If the animation only has 1 frame, display it like a normal image.
            if movie.frameCount() <= 1:
                self._display_fallback_image(filepath, ext)
                return stats

            # The animation has more than 1 frame, continue displaying it as an animation
            self.switch_preview("animated")
            self.resizeEvent(
                QResizeEvent(
                    QSize(stats["width"], stats["height"]),
                    QSize(stats["width"], stats["height"]),
                )
            )
            movie.start()

            stats["duration"] = movie.frameCount() // 60
        except (UnidentifiedImageError, FileNotFoundError) as e:
            logger.error("[PreviewThumb] Could not load animated image", filepath=filepath, error=e)
            return self._display_fallback_image(filepath, ext)

        return stats

    def _get_video_res(self, filepath: str) -> tuple[bool, QSize]:
        video = cv2.VideoCapture(filepath, cv2.CAP_FFMPEG)
        success, frame = video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        return (success, QSize(image.width, image.height))

    def _update_media(self, filepath: Path, type: MediaType) -> dict[str, int]:
        stats: dict[str, int] = {}

        self.media_player.play(filepath)

        if type == MediaType.VIDEO:
            try:
                success, size = self._get_video_res(str(filepath))
                if success:
                    self.update_image_size(
                        (size.width(), size.height()), size.width() / size.height()
                    )
                    self.resizeEvent(
                        QResizeEvent(
                            QSize(size.width(), size.height()),
                            QSize(size.width(), size.height()),
                        )
                    )

                    stats["width"] = size.width()
                    stats["height"] = size.height()

            except cv2.error as e:
                logger.error("[PreviewThumb] Could not play video", filepath=filepath, error=e)

        self.switch_preview("video" if type == MediaType.VIDEO else "audio")
        stats["duration"] = self.media_player.player.duration() * 1000
        return stats

    def update_preview(self, filepath: Path) -> dict[str, int]:
        """Render a single file preview."""
        ext = filepath.suffix.lower()
        stats: dict[str, int] = {}

        # Video
        if MediaCategories.is_ext_in_category(
            ext, MediaCategories.VIDEO_TYPES, mime_fallback=True
        ) and is_readable_video(filepath):
            stats = self._update_media(filepath, MediaType.VIDEO)

        # Audio
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.AUDIO_TYPES, mime_fallback=True
        ):
            self._update_image(filepath)
            stats = self._update_media(filepath, MediaType.AUDIO)
            self.thumb_renderer.render(
                time.time(),
                filepath,
                (512, 512),
                self.devicePixelRatio(),
                update_on_ratio_change=True,
            )

        # Animated Images
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.IMAGE_ANIMATED_TYPES, mime_fallback=True
        ):
            stats = self._update_animation(filepath, ext)

        # Other Types (Including Images)
        else:
            # TODO: Get thumb renderer to return this stuff to pass on
            stats = self._update_image(filepath)

            self.thumb_renderer.render(
                time.time(),
                filepath,
                (512, 512),
                self.devicePixelRatio(),
                update_on_ratio_change=True,
            )

        with catch_warnings(record=True):
            self.preview_img.clicked.disconnect()
        self.preview_img.clicked.connect(lambda checked=False, path=filepath: open_file(path))
        self.preview_img.is_connected = True

        self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.preview_img.setCursor(Qt.CursorShape.PointingHandCursor)

        self.opener = FileOpenerHelper(filepath)
        self.open_file_action.triggered.connect(self.opener.open_file)
        self.open_explorer_action.triggered.connect(self.opener.open_explorer)

        with catch_warnings(record=True):
            self.delete_action.triggered.disconnect()

        self.delete_action.setText(
            Translations.format("trash.context.singular", trash_term=trash_term())
        )
        self.delete_action.triggered.connect(
            lambda checked=False, f=filepath: self.driver.delete_files_callback(f)
        )
        self.delete_action.setEnabled(bool(filepath))

        return stats

    def hide_preview(self) -> None:
        """Completely hide the file preview."""
        self.switch_preview("")

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.update_image_size((self.size().width(), self.size().height()))
        return super().resizeEvent(event)
