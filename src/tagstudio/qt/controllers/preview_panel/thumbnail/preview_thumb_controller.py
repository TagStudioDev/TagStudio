# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import io
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import rawpy
import structlog
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QResizeEvent

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaCategories
from tagstudio.qt.helpers.file_tester import is_readable_video
from tagstudio.qt.utils.file_opener import open_file
from tagstudio.qt.views.preview_panel.thumbnail.preview_thumb_view import PreviewThumbView

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)
Image.MAX_IMAGE_PIXELS = None


class PreviewThumb(PreviewThumbView):
    dimensions_changed = Signal(QSize)
    duration_changed = Signal(int)

    __current_file: Path

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__(library, driver)

        self.__driver: QtDriver = driver

        self._media_player.duration_changed.connect(self.duration_changed.emit)

    def _on_dimensions_change(self, size: QSize | None) -> None:
        if size is None:
            size = QSize(0, 0)

        self.resizeEvent(QResizeEvent(size, size))
        self.dimensions_changed.emit(size)

    def __get_image_size(self, filepath: Path) -> QSize:
        """Get width and height of an image as dict."""
        size = QSize()
        ext = filepath.suffix.lower()

        if filepath.is_dir():
            pass
        elif MediaCategories.IMAGE_RAW_TYPES.contains(ext, mime_fallback=True):
            try:
                with rawpy.imread(str(filepath)) as raw:
                    rgb = raw.postprocess()
                    image = Image.new("L", (rgb.shape[1], rgb.shape[0]), color="black")
                    size = QSize(image.width, image.height)
            except (
                rawpy._rawpy._rawpy.LibRawIOError,  # pyright: ignore[reportAttributeAccessIssue]
                rawpy._rawpy.LibRawFileUnsupportedError,  # pyright: ignore[reportAttributeAccessIssue]
                FileNotFoundError,
            ):
                pass
        elif MediaCategories.IMAGE_RASTER_TYPES.contains(ext, mime_fallback=True):
            try:
                image = Image.open(str(filepath))
                size = QSize(image.width, image.height)
            except (
                DecompressionBombError,
                FileNotFoundError,
                NotImplementedError,
                UnidentifiedImageError,
            ) as e:
                logger.error("[PreviewThumb] Could not get image stats", filepath=filepath, error=e)
        elif MediaCategories.IMAGE_VECTOR_TYPES.contains(ext, mime_fallback=True):
            pass  # TODO

        return size

    def __get_gif_data(self, filepath: Path) -> tuple[bytes, QSize] | None:
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
                return image_bytes_io.read(), QSize(image.width, image.height)
            else:
                image.close()
                with open(filepath, "rb") as f:
                    return f.read(), QSize(image.width, image.height)

        except (UnidentifiedImageError, FileNotFoundError) as e:
            logger.error("[PreviewThumb] Could not load animated image", filepath=filepath, error=e)
            return None

    def __get_video_res(self, filepath: str) -> tuple[bool, QSize]:
        video = cv2.VideoCapture(filepath, cv2.CAP_FFMPEG)
        success, frame = video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        return success, QSize(image.width, image.height)

    def display_file(self, filepath: Path) -> None:
        """Render a single file preview."""
        self.__current_file = filepath

        ext = filepath.suffix.lower()

        # Video
        if MediaCategories.VIDEO_TYPES.contains(ext, mime_fallback=True) and is_readable_video(
            filepath
        ):
            video_size: QSize | None = None
            try:
                success, video_size = self.__get_video_res(str(filepath))
                if not success:
                    video_size = None
            except cv2.error as e:
                logger.error("[PreviewThumb] Could not play video", filepath=filepath, error=e)

            self._display_video(filepath, video_size)
            self._on_dimensions_change(video_size)

        # Audio
        elif MediaCategories.AUDIO_TYPES.contains(ext, mime_fallback=True):
            self._display_audio(filepath)

        # Animated Images
        elif MediaCategories.IMAGE_ANIMATED_TYPES.contains(ext, mime_fallback=True):
            gif_data = self.__get_gif_data(filepath)
            if gif_data:
                self._display_gif(*gif_data)
                gif_size = gif_data[1]
            else:
                self._display_image(filepath)
                gif_size = self.__get_image_size(filepath)

            self._on_dimensions_change(gif_size)

        # Other Types (Including Images)
        else:
            self._display_image(filepath)

            image_size: QSize = self.__get_image_size(filepath)
            self._on_dimensions_change(image_size)

    def _open_file_action_callback(self):
        open_file(
            self.__current_file, windows_start_command=self.__driver.settings.windows_start_command
        )

    def _open_explorer_action_callback(self):
        open_file(self.__current_file, file_manager=True)

    def _delete_action_callback(self):
        if bool(self.__current_file):
            self.__driver.delete_files_callback(self.__current_file)

    def _button_wrapper_callback(self):
        open_file(
            self.__current_file, windows_start_command=self.__driver.settings.windows_start_command
        )
