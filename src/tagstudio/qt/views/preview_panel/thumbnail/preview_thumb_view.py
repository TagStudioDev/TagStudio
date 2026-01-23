# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import math
import time
from pathlib import Path
from typing import TYPE_CHECKING, override

import structlog
from PySide6.QtCore import QBuffer, QByteArray, QSize, Qt
from PySide6.QtGui import QAction, QMovie, QPixmap, QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedLayout, QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaType
from tagstudio.qt.mixed.preview_panel.thumbnail.media_player import MediaPlayer
from tagstudio.qt.platform_strings import open_file_str, trash_term
from tagstudio.qt.previews.renderer import ThumbRenderer
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.styles.rounded_pixmap_style import RoundedPixmapStyle

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


THUMB_SIZE_FACTOR = 2


class PreviewThumbView(QWidget):
    """The Preview Panel Widget."""

    __thumbnail_button_size: tuple[int, int]
    __thumbnail_ratio: float

    __filepath: Path | None
    __rendered_res: tuple[int, int]

    def __init__(self, library: Library, driver: "QtDriver") -> None:
        super().__init__()

        self.__thumbnail_button_size = (266, 266)
        self.__thumbnail_ratio = 1.0

        self.__thumb_layout = QStackedLayout(self)
        self.__thumb_layout.setObjectName("thumbnail_layout")
        self.__thumb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__thumb_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.__thumb_layout.setContentsMargins(0, 0, 0, 0)

        open_file_action = QAction(Translations["file.open_file"], self)
        open_file_action.triggered.connect(self._open_file_action_callback)
        open_explorer_action = QAction(open_file_str(), self)
        open_explorer_action.triggered.connect(self._open_explorer_action_callback)
        delete_action = QAction(
            Translations.format("trash.context.singular", trash_term=trash_term()),
            self,
        )
        delete_action.triggered.connect(self._delete_action_callback)

        self.__button_wrapper = QPushButton()
        self.__button_wrapper.setMinimumSize(*self.__thumbnail_button_size)
        self.__button_wrapper.setFlat(True)
        self.__button_wrapper.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.__button_wrapper.addAction(open_file_action)
        self.__button_wrapper.addAction(open_explorer_action)
        self.__button_wrapper.addAction(delete_action)
        self.__button_wrapper.clicked.connect(self._button_wrapper_callback)

        # Image preview
        # In testing, it didn't seem possible to center the widgets directly
        # on the QStackedLayout. Adding sublayouts allows us to center the widgets.
        self.__preview_img_page = QWidget()
        self.__preview_img_page.setObjectName("image_preview_page")

        self.__stacked_page_setup(self.__preview_img_page, self.__button_wrapper)
        self.__thumb_layout.addWidget(self.__preview_img_page)

        # GIF preview
        self.__preview_gif = QLabel()
        self.__preview_gif.setObjectName("gif_preview")
        self.__preview_gif.setMinimumSize(*self.__thumbnail_button_size)
        self.__preview_gif.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.__preview_gif.setCursor(Qt.CursorShape.ArrowCursor)
        self.__preview_gif.addAction(open_file_action)
        self.__preview_gif.addAction(open_explorer_action)
        self.__preview_gif.addAction(delete_action)
        self.__gif_buffer: QBuffer = QBuffer()

        self.__preview_gif_page = QWidget()
        self.__preview_gif_page.setObjectName("gif_preview_page")

        self.__stacked_page_setup(self.__preview_gif_page, self.__preview_gif)
        self.__thumb_layout.addWidget(self.__preview_gif_page)

        # Media preview
        self._media_player = MediaPlayer(driver)
        self._media_player.addAction(open_file_action)
        self._media_player.addAction(open_explorer_action)
        self._media_player.addAction(delete_action)

        # Need to watch for this to resize the player appropriately.
        self._media_player.player.hasVideoChanged.connect(
            self.__media_player_video_changed_callback
        )

        self.__media_player_page = QWidget()
        self.__media_player_page.setObjectName("media_preview_page")

        self.__stacked_page_setup(self.__media_player_page, self._media_player)
        self.__thumb_layout.addWidget(self.__media_player_page)

        # Thumbnail renderer
        self.__thumb_renderer = ThumbRenderer(driver)
        self.__thumb_renderer.updated.connect(self.__thumb_renderer_updated_callback)
        self.__thumb_renderer.updated_ratio.connect(self.__thumb_renderer_updated_ratio_callback)

        self.setMinimumSize(*self.__thumbnail_button_size)
        self.hide_preview()

    def _open_file_action_callback(self):
        raise NotImplementedError

    def _open_explorer_action_callback(self):
        raise NotImplementedError

    def _delete_action_callback(self):
        raise NotImplementedError

    def _button_wrapper_callback(self):
        raise NotImplementedError

    def __media_player_video_changed_callback(self, video: bool) -> None:
        self.__update_thumbnail_size(self.size())

    def __thumb_renderer_updated_callback(
        self, _timestamp: float, img: QPixmap, _size: QSize, _path: Path
    ) -> None:
        self.__button_wrapper.setIcon(img)

    def __thumb_renderer_updated_ratio_callback(self, ratio: float) -> None:
        self.__thumbnail_ratio = ratio
        self.__update_thumbnail_size(self.size())

    def __stacked_page_setup(self, page: QWidget, widget: QWidget) -> None:
        layout = QHBoxLayout(page)
        layout.addWidget(widget)
        layout.setAlignment(widget, Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        page.setLayout(layout)

    def __update_thumbnail_size(self, size: QSize) -> None:
        adj_width: float = size.width()
        adj_height: float = size.height()
        # Landscape
        if self.__thumbnail_ratio > 1:
            adj_height = size.width() * (1 / self.__thumbnail_ratio)
        # Portrait
        elif self.__thumbnail_ratio <= 1:
            adj_width = size.height() * self.__thumbnail_ratio

        if adj_width > size.width():
            adj_height = adj_height * (size.width() / adj_width)
            adj_width = size.width()
        elif adj_height > size.height():
            adj_width = adj_width * (size.height() / adj_height)
            adj_height = size.height()

        adj_size: QSize = QSize(int(adj_width), int(adj_height))

        self.__thumbnail_button_size = (adj_size.width(), adj_size.height())
        self.__button_wrapper.setMaximumSize(adj_size)
        self.__button_wrapper.setIconSize(adj_size)
        self.__preview_gif.setMaximumSize(adj_size)
        self.__preview_gif.setMinimumSize(adj_size)

        self._media_player.setMaximumSize(adj_size)
        self._media_player.setMinimumSize(adj_size)

        proxy_style = RoundedPixmapStyle(radius=8)
        self.__preview_gif.setStyle(proxy_style)
        self._media_player.setStyle(proxy_style)
        m = self.__preview_gif.movie()
        if m:
            m.setScaledSize(adj_size)

    def __switch_preview(self, preview: MediaType | None) -> None:
        if preview in [MediaType.AUDIO, MediaType.VIDEO]:
            self._media_player.show()
            self.__thumb_layout.setCurrentWidget(self.__media_player_page)
        else:
            self._media_player.stop()
            self._media_player.hide()

        if preview in [MediaType.IMAGE, MediaType.AUDIO]:
            self.__button_wrapper.show()
            self.__thumb_layout.setCurrentWidget(
                self.__preview_img_page if preview == MediaType.IMAGE else self.__media_player_page
            )
        else:
            self.__button_wrapper.hide()

        if preview == MediaType.IMAGE_ANIMATED:
            self.__preview_gif.show()
            self.__thumb_layout.setCurrentWidget(self.__preview_gif_page)
        else:
            if self.__preview_gif.movie():
                self.__preview_gif.movie().stop()
                self.__gif_buffer.close()
            self.__preview_gif.hide()

    def __render_thumb(self, filepath: Path) -> None:
        self.__filepath = filepath
        self.__rendered_res = (
            math.ceil(self.__thumbnail_button_size[0] * THUMB_SIZE_FACTOR),
            math.ceil(self.__thumbnail_button_size[1] * THUMB_SIZE_FACTOR),
        )

        self.__thumb_renderer.render(
            time.time(),
            filepath,
            self.__rendered_res,
            self.devicePixelRatio(),
            update_on_ratio_change=True,
        )

    def __update_media_player(self, filepath: Path) -> None:
        """Display either audio or video.

        Returns the duration of the audio / video.
        """
        self._media_player.play(filepath)

    def _display_video(self, filepath: Path, size: QSize | None) -> None:
        logger.debug("[PreviewThumbView][_display_image] Displaying video", path=filepath)
        self.__switch_preview(MediaType.VIDEO)
        self.__update_media_player(filepath)

    def _display_audio(self, filepath: Path) -> None:
        logger.debug("[PreviewThumbView][_display_image] Displaying audio", path=filepath)
        self.__switch_preview(MediaType.AUDIO)
        self.__render_thumb(filepath)
        self.__update_media_player(filepath)

    def _display_gif(self, gif_data: bytes, size: QSize) -> bool:
        """Update the animated image preview from a filepath."""
        # Ensure that any movie and buffer from previous animations are cleared.
        if self.__preview_gif.movie():
            self.__preview_gif.movie().stop()
            self.__gif_buffer.close()

        self.__thumbnail_ratio = size.width() / size.height()

        self.__gif_buffer.setData(gif_data)
        movie = QMovie(self.__gif_buffer, QByteArray())
        self.__preview_gif.setMovie(movie)

        logger.debug(
            "[PreviewThumbView][_display_gif] Displaying GIF", frame_count=movie.frameCount()
        )

        # If the animation only has 1 frame, it isn't animated and shouldn't be treated as such
        if movie.frameCount() <= 1:
            return False

        # The animation has more than 1 frame, continue displaying it as an animation
        self.__switch_preview(MediaType.IMAGE_ANIMATED)
        movie.start()
        return True

    def _display_image(self, filepath: Path) -> None:
        """Renders the given file as an image, no matter its media type."""
        logger.debug("[PreviewThumbView][_display_image] Displaying image", path=filepath)
        self.__switch_preview(MediaType.IMAGE)
        self.__render_thumb(filepath)

    def hide_preview(self) -> None:
        """Completely hide the file preview."""
        self.__switch_preview(None)
        self.__filepath = None

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.__update_thumbnail_size(self.size())

        if self.__filepath is not None and self.__rendered_res < self.__thumbnail_button_size:
            self.__render_thumb(self.__filepath)

        return super().resizeEvent(event)

    @property
    def media_player(self) -> MediaPlayer:
        return self._media_player
