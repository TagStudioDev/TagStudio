# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import io
import time
from pathlib import Path
from typing import TYPE_CHECKING, override

import cv2
import structlog
from PIL import Image, UnidentifiedImageError
from PySide6.QtCore import QBuffer, QByteArray, QSize, Qt
from PySide6.QtGui import QAction, QMovie, QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QStackedLayout, QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaType
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


class PreviewThumbView(QWidget):
    """The Preview Panel Widget."""

    def __init__(self, library: Library, driver: "QtDriver") -> None:
        super().__init__()

        self.lib = library
        self.driver: QtDriver = driver

        self.__img_button_size: tuple[int, int] = (266, 266)
        self.__image_ratio: float = 1.0

        self.__image_layout = QStackedLayout(self)
        self.__image_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__image_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.__image_layout.setContentsMargins(0, 0, 0, 0)

        self.__open_file_action = QAction(Translations["file.open_file"], self)
        self.__open_file_action.triggered.connect(self._open_file_action_callback)
        self.__open_explorer_action = QAction(open_file_str(), self)
        self.__open_explorer_action.triggered.connect(self._open_explorer_action_callback)
        self.__delete_action = QAction(
            Translations.format("trash.context.singular", trash_term=trash_term()),
            self,
        )
        self.__delete_action.triggered.connect(self._delete_action_callback)

        self.__button_wrapper = QPushButtonWrapper()
        self.__button_wrapper.setMinimumSize(*self.__img_button_size)
        self.__button_wrapper.setFlat(True)
        self.__button_wrapper.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.__button_wrapper.addAction(self.__open_file_action)
        self.__button_wrapper.addAction(self.__open_explorer_action)
        self.__button_wrapper.addAction(self.__delete_action)
        self.__button_wrapper.clicked.connect(self._button_wrapper_callback)

        # In testing, it didn't seem possible to center the widgets directly
        # on the QStackedLayout. Adding sublayouts allows us to center the widgets.
        self.preview_img_page = QWidget()
        self.__stacked_page_setup(self.preview_img_page, self.__button_wrapper)

        self.__preview_gif = QLabel()
        self.__preview_gif.setMinimumSize(*self.__img_button_size)
        self.__preview_gif.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.__preview_gif.setCursor(Qt.CursorShape.ArrowCursor)
        self.__preview_gif.addAction(self.__open_file_action)
        self.__preview_gif.addAction(self.__open_explorer_action)
        self.__preview_gif.addAction(self.__delete_action)
        self.__gif_buffer: QBuffer = QBuffer()

        self.__preview_gif_page = QWidget()
        self.__stacked_page_setup(self.__preview_gif_page, self.__preview_gif)

        self.__media_player = MediaPlayer(driver)
        self.__media_player.addAction(self.__open_file_action)
        self.__media_player.addAction(self.__open_explorer_action)
        self.__media_player.addAction(self.__delete_action)

        # Need to watch for this to resize the player appropriately.
        self.__media_player.player.hasVideoChanged.connect(self.__has_video_changed)

        self.__mp_max_size = QSize(*self.__img_button_size)

        self.__media_player_page = QWidget()
        self.__stacked_page_setup(self.__media_player_page, self.__media_player)

        self.__thumb_renderer = ThumbRenderer(self.lib)
        self.__thumb_renderer.updated.connect(
            lambda ts, i, s: (
                self.__button_wrapper.setIcon(i),
                self.__set_mp_max_size(i.size()),
            )
        )
        self.__thumb_renderer.updated_ratio.connect(
            lambda ratio: (
                self.__set_image_ratio(ratio),
                self.__update_image_size(
                    (
                        self.size().width(),
                        self.size().height(),
                    ),
                    ratio,
                ),
            )
        )

        self.__image_layout.addWidget(self.preview_img_page)
        self.__image_layout.addWidget(self.__preview_gif_page)
        self.__image_layout.addWidget(self.__media_player_page)

        self.setMinimumSize(*self.__img_button_size)

        self.hide_preview()

    def _open_file_action_callback(self):
        raise NotImplementedError

    def _open_explorer_action_callback(self):
        raise NotImplementedError

    def _delete_action_callback(self):
        raise NotImplementedError

    def _button_wrapper_callback(self):
        raise NotImplementedError

    def __set_mp_max_size(self, size: QSize) -> None:
        self.__mp_max_size = size

    def __has_video_changed(self, video: bool) -> None:
        self.__update_image_size((self.size().width(), self.size().height()))

    def __stacked_page_setup(self, page: QWidget, widget: QWidget) -> None:
        layout = QHBoxLayout(page)
        layout.addWidget(widget)
        layout.setAlignment(widget, Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        page.setLayout(layout)

    def __set_image_ratio(self, ratio: float) -> None:
        self.__image_ratio = ratio

    def __update_image_size(self, size: tuple[int, int], ratio: float | None = None) -> None:
        if ratio:
            self.__set_image_ratio(ratio)

        adj_width: float = size[0]
        adj_height: float = size[1]
        # Landscape
        if self.__image_ratio > 1:
            adj_height = size[0] * (1 / self.__image_ratio)
        # Portrait
        elif self.__image_ratio <= 1:
            adj_width = size[1] * self.__image_ratio

        if adj_width > size[0]:
            adj_height = adj_height * (size[0] / adj_width)
            adj_width = size[0]
        elif adj_height > size[1]:
            adj_width = adj_width * (size[1] / adj_height)
            adj_height = size[1]

        adj_size = QSize(int(adj_width), int(adj_height))

        self.__img_button_size = (int(adj_width), int(adj_height))
        self.__button_wrapper.setMaximumSize(adj_size)
        self.__button_wrapper.setIconSize(adj_size)
        self.__preview_gif.setMaximumSize(adj_size)
        self.__preview_gif.setMinimumSize(adj_size)

        if not self.__media_player.player.hasVideo():
            # ensure we do not exceed the thumbnail size
            mp_width = (
                adj_size.width()
                if adj_size.width() < self.__mp_max_size.width()
                else self.__mp_max_size.width()
            )
            mp_height = (
                adj_size.height()
                if adj_size.height() < self.__mp_max_size.height()
                else self.__mp_max_size.height()
            )
            mp_size = QSize(mp_width, mp_height)
            self.__media_player.setMinimumSize(mp_size)
            self.__media_player.setMaximumSize(mp_size)
        else:
            # have video, so just resize as normal
            self.__media_player.setMaximumSize(adj_size)
            self.__media_player.setMinimumSize(adj_size)

        proxy_style = RoundedPixmapStyle(radius=8)
        self.__preview_gif.setStyle(proxy_style)
        self.__media_player.setStyle(proxy_style)
        m = self.__preview_gif.movie()
        if m:
            m.setScaledSize(adj_size)

    def __switch_preview(self, preview: MediaType | None) -> None:
        if preview in [MediaType.AUDIO, MediaType.VIDEO]:
            self.__media_player.show()
            self.__image_layout.setCurrentWidget(self.__media_player_page)
        else:
            self.__media_player.stop()
            self.__media_player.hide()

        if preview in [MediaType.IMAGE, MediaType.AUDIO]:
            self.__button_wrapper.show()
            self.__image_layout.setCurrentWidget(
                self.preview_img_page if preview == MediaType.IMAGE else self.__media_player_page
            )
        else:
            self.__button_wrapper.hide()

        if preview == MediaType.IMAGE_ANIMATED:
            self.__preview_gif.show()
            self.__image_layout.setCurrentWidget(self.__preview_gif_page)
        else:
            if self.__preview_gif.movie():
                self.__preview_gif.movie().stop()
                self.__gif_buffer.close()
            self.__preview_gif.hide()

    def __get_video_res(self, filepath: str) -> tuple[bool, QSize]:
        video = cv2.VideoCapture(filepath, cv2.CAP_FFMPEG)
        success, frame = video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        return (success, QSize(image.width, image.height))

    def __display_av_media(self, filepath: Path, type: MediaType) -> dict[str, int]:
        """Display either audio or video."""
        stats: dict[str, int] = {}

        self.__media_player.play(filepath)

        if type == MediaType.VIDEO:
            try:
                success, size = self.__get_video_res(str(filepath))
                if success:
                    self.__update_image_size(
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
        else:
            self.__thumb_renderer.render(
                time.time(),
                filepath,
                (512, 512),
                self.devicePixelRatio(),
                update_on_ratio_change=True,
            )

        self.__switch_preview(type)
        stats["duration"] = self.__media_player.player.duration() * 1000
        return stats

    def _display_video(self, filepath: Path) -> dict[str, int]:
        return self.__display_av_media(filepath, MediaType.VIDEO)

    def _display_audio(self, filepath: Path) -> dict[str, int]:
        return self.__display_av_media(filepath, MediaType.AUDIO)

    def _display_animated_image(self, filepath: Path) -> dict[str, int] | None:
        """Update the animated image preview from a filepath."""
        ext = filepath.suffix.lower()
        stats: dict[str, int] = {}

        # Ensure that any movie and buffer from previous animations are cleared.
        if self.__preview_gif.movie():
            self.__preview_gif.movie().stop()
            self.__gif_buffer.close()

        try:
            image: Image.Image = Image.open(filepath)
            stats["width"] = image.width
            stats["height"] = image.height

            self.__update_image_size((image.width, image.height), image.width / image.height)
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
                self.__gif_buffer.setData(image_bytes_io.read())
            else:
                image.close()
                with open(filepath, "rb") as f:
                    self.__gif_buffer.setData(f.read())
            movie = QMovie(self.__gif_buffer, QByteArray())
            self.__preview_gif.setMovie(movie)

            # If the animation only has 1 frame, display it like a normal image.
            if movie.frameCount() <= 1:
                self._display_image(filepath)
                return stats

            # The animation has more than 1 frame, continue displaying it as an animation
            self.__switch_preview(MediaType.IMAGE_ANIMATED)
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
            return None

        return stats

    def _display_image(self, filepath: Path):
        """Renders the given file as an image, no matter its media type."""
        self.__switch_preview(MediaType.IMAGE)
        self.__thumb_renderer.render(
            time.time(),
            filepath,
            (512, 512),
            self.devicePixelRatio(),
            update_on_ratio_change=True,
        )

    def hide_preview(self) -> None:
        """Completely hide the file preview."""
        self.__switch_preview(None)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.__update_image_size((self.size().width(), self.size().height()))
        return super().resizeEvent(event)

    @property
    def media_player(self) -> MediaPlayer:
        return self.__media_player
