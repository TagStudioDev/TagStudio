# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import io
import time
import typing
from pathlib import Path

import cv2
import rawpy
import structlog
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import QBuffer, QByteArray, QSize, Qt, Signal
from PySide6.QtGui import QMovie, QResizeEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
)
from src.core.library.alchemy.library import Library
from src.core.library.alchemy.models import Entry
from src.core.media_types import MediaCategories
from src.qt.helpers.file_opener import FileOpenerHelper, open_file
from src.qt.helpers.file_tester import is_readable_video
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper
from src.qt.helpers.rounded_pixmap_style import RoundedPixmapStyle
from src.qt.translations import Translations
from src.qt.widgets.media_player import MediaPlayer
from src.qt.widgets.thumb_renderer import ThumbRenderer
from src.qt.widgets.video_player import VideoPlayer

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class PreviewThumb(QWidget):
    """The Preview Panel Widget."""

    tags_updated = Signal()

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()

        self.is_connected = False
        self.lib = library
        self.driver: QtDriver = driver

        self.img_button_size: tuple[int, int] = (266, 266)
        self.image_ratio: float = 1.0

        # self.panel_bg_color = (
        #     Theme.COLOR_BG_DARK.value
        #     if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        #     else Theme.COLOR_BG_LIGHT.value
        # )

        self.image_container = QWidget()
        image_layout = QHBoxLayout(self.image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)

        # self.open_file_action = QAction("Open file", self)
        # self.open_explorer_action = QAction(PlatformStrings.open_file_str, self)

        self.preview_img = QPushButtonWrapper()
        self.preview_img.setMinimumSize(*self.img_button_size)
        self.preview_img.setFlat(True)
        self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        # self.preview_img.addAction(self.open_file_action)
        # self.preview_img.addAction(self.open_explorer_action)

        self.preview_gif = QLabel()
        self.preview_gif.setMinimumSize(*self.img_button_size)
        self.preview_gif.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.preview_gif.setCursor(Qt.CursorShape.ArrowCursor)
        # self.preview_gif.addAction(self.open_file_action)
        # self.preview_gif.addAction(self.open_explorer_action)
        self.preview_gif.hide()
        self.gif_buffer: QBuffer = QBuffer()

        self.preview_vid = VideoPlayer(driver)
        self.preview_vid.hide()
        self.thumb_renderer = ThumbRenderer()
        self.thumb_renderer.updated.connect(lambda ts, i, s: (self.preview_img.setIcon(i)))
        self.thumb_renderer.updated_ratio.connect(
            lambda ratio: (
                self.set_image_ratio(ratio),
                self.update_image_size(
                    (
                        self.image_container.size().width(),
                        self.image_container.size().height(),
                    ),
                    ratio,
                ),
            )
        )

        self.media_player = MediaPlayer(driver)
        self.media_player.hide()

        image_layout.addWidget(self.preview_img)
        image_layout.setAlignment(self.preview_img, Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.preview_gif)
        image_layout.setAlignment(self.preview_gif, Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.preview_vid)
        image_layout.setAlignment(self.preview_vid, Qt.AlignmentFlag.AlignCenter)
        self.image_container.setMinimumSize(*self.img_button_size)

    def set_image_ratio(self, ratio: float):
        self.image_ratio = ratio

    def update_image_size(self, size: tuple[int, int], ratio: float = None):
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
        self.preview_vid.resize_video(adj_size)
        self.preview_vid.setMaximumSize(adj_size)
        self.preview_vid.setMinimumSize(adj_size)
        self.preview_gif.setMaximumSize(adj_size)
        self.preview_gif.setMinimumSize(adj_size)
        proxy_style = RoundedPixmapStyle(radius=8)
        self.preview_gif.setStyle(proxy_style)
        self.preview_vid.setStyle(proxy_style)
        m = self.preview_gif.movie()
        if m:
            m.setScaledSize(adj_size)

    def get_preview_size(self) -> tuple[int, int]:
        return (
            self.image_container.size().width(),
            self.image_container.size().height(),
        )

    def update_preview(self, entry: Entry, filepath: Path) -> dict:
        """Render a single file preview."""
        # self.tag_callback = tag_callback if tag_callback else None

        # # update list of libraries
        # self.fill_libs_widget(self.libs_layout)

        # self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        # self.preview_img.setCursor(Qt.CursorShape.ArrowCursor)

        # ratio = self.devicePixelRatio()
        # self.thumb_renderer.render(
        #     time.time(),
        #     "",
        #     (512, 512),
        #     ratio,
        #     is_loading=True,
        #     update_on_ratio_change=True,
        # )
        # if self.preview_img.is_connected:
        #     self.preview_img.clicked.disconnect()
        # self.preview_img.show()
        # self.preview_vid.stop()
        # self.preview_vid.hide()
        # self.media_player.hide()
        # self.media_player.stop()
        # self.preview_gif.hide()
        # self.selected = list(self.driver.selected)
        # self.add_field_button.setHidden(True)

        # reload entry and fill it into the grid again
        # 1 Selected Entry
        # selected_idx = self.driver.selected[0]
        # item = self.driver.frame_content[selected_idx]

        self.preview_img.show()
        self.preview_vid.stop()
        self.preview_vid.hide()
        self.media_player.stop()
        self.media_player.hide()
        self.preview_gif.hide()

        # If a new selection is made, update the thumbnail and filepath.
        ratio = self.devicePixelRatio()
        self.thumb_renderer.render(
            time.time(),
            filepath,
            (512, 512),
            ratio,
            update_on_ratio_change=True,
        )

        self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.preview_img.setCursor(Qt.CursorShape.PointingHandCursor)

        self.opener = FileOpenerHelper(filepath)
        # self.open_file_action.triggered.connect(self.opener.open_file)
        # self.open_explorer_action.triggered.connect(self.opener.open_explorer)

        # TODO: Do this all somewhere else, this is just here temporarily.
        ext: str = filepath.suffix.lower()
        try:
            if MediaCategories.is_ext_in_category(
                ext, MediaCategories.IMAGE_ANIMATED_TYPES, mime_fallback=True
            ):
                if self.preview_gif.movie():
                    self.preview_gif.movie().stop()
                    self.gif_buffer.close()

            image: Image.Image = Image.open(filepath)
            anim_image: Image.Image = image
            image_bytes_io: io.BytesIO = io.BytesIO()
            anim_image.save(
                image_bytes_io,
                "GIF",
                lossless=True,
                save_all=True,
                loop=0,
                disposal=2,
            )
            image_bytes_io.seek(0)
            ba: bytes = image_bytes_io.read()

            self.gif_buffer.setData(ba)
            movie = QMovie(self.gif_buffer, QByteArray())
            self.preview_gif.setMovie(movie)
            movie.start()

            self.resizeEvent(
                QResizeEvent(
                    QSize(image.width, image.height),
                    QSize(image.width, image.height),
                )
            )
            self.preview_img.hide()
            self.preview_vid.hide()
            self.preview_gif.show()

            image = None
            if MediaCategories.is_ext_in_category(ext, MediaCategories.IMAGE_RASTER_TYPES):
                image = Image.open(str(filepath))
            elif MediaCategories.is_ext_in_category(ext, MediaCategories.IMAGE_RAW_TYPES):
                try:
                    with rawpy.imread(str(filepath)) as raw:
                        rgb = raw.postprocess()
                        image = Image.new("L", (rgb.shape[1], rgb.shape[0]), color="black")
                except (
                    rawpy._rawpy.LibRawIOError,
                    rawpy._rawpy.LibRawFileUnsupportedError,
                ):
                    pass
            elif MediaCategories.is_ext_in_category(ext, MediaCategories.AUDIO_TYPES):
                self.media_player.show()
                self.media_player.play(filepath)
            elif MediaCategories.is_ext_in_category(
                ext, MediaCategories.VIDEO_TYPES
            ) and is_readable_video(filepath):
                video = cv2.VideoCapture(str(filepath), cv2.CAP_FFMPEG)
                video.set(
                    cv2.CAP_PROP_POS_FRAMES,
                    (video.get(cv2.CAP_PROP_FRAME_COUNT) // 2),
                )
                success, frame = video.read()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                if success:
                    self.preview_img.hide()
                    self.preview_vid.play(str(filepath), QSize(image.width, image.height))
                    self.resizeEvent(
                        QResizeEvent(
                            QSize(image.width, image.height),
                            QSize(image.width, image.height),
                        )
                    )
                    self.preview_vid.show()

        except (FileNotFoundError, cv2.error, UnidentifiedImageError, DecompressionBombError) as e:
            if self.preview_img.is_connected:
                self.preview_img.clicked.disconnect()
            self.preview_img.clicked.connect(lambda checked=False, pth=filepath: open_file(pth))
            self.preview_img.is_connected = True
            logger.error(f"Preview thumb error: {e} - {filepath}")

        return {}
