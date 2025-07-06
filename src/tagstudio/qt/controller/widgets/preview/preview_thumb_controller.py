# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path
from typing import TYPE_CHECKING

import rawpy
import structlog
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaCategories
from tagstudio.qt.helpers.file_opener import open_file
from tagstudio.qt.helpers.file_tester import is_readable_video
from tagstudio.qt.view.widgets.preview.preview_thumb_view import PreviewThumbView

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class PreviewThumb(PreviewThumbView):
    __current_file: Path

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__(library, driver)

    def __get_image_stats(self, filepath: Path) -> dict[str, int]:
        """Get width and height of an image as dict."""
        stats: dict[str, int] = {}
        ext = filepath.suffix.lower()

        if MediaCategories.IMAGE_RAW_TYPES.contains(ext, mime_fallback=True):
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
        elif MediaCategories.IMAGE_RASTER_TYPES.contains(ext, mime_fallback=True):
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
        elif MediaCategories.IMAGE_VECTOR_TYPES.contains(ext, mime_fallback=True):
            pass  # TODO

        return stats

    def display_file(self, filepath: Path) -> dict[str, int]:
        """Render a single file preview."""
        self.__current_file = filepath

        ext = filepath.suffix.lower()

        # Video
        if MediaCategories.VIDEO_TYPES.contains(ext, mime_fallback=True) and is_readable_video(
            filepath
        ):
            return self._display_video(filepath)
        # Audio
        elif MediaCategories.AUDIO_TYPES.contains(ext, mime_fallback=True):
            return self._display_audio(filepath)
        # Animated Images
        elif MediaCategories.IMAGE_ANIMATED_TYPES.contains(ext, mime_fallback=True):
            if (stats := self._display_animated_image(filepath)) is not None:
                return stats
            else:
                self._display_image(filepath)
                return self.__get_image_stats(filepath)
        # Other Types (Including Images)
        else:
            self._display_image(filepath)
            return self.__get_image_stats(filepath)

    def _open_file_action_callback(self):
        open_file(self.__current_file)

    def _open_explorer_action_callback(self):
        open_file(self.__current_file, file_manager=True)

    def _delete_action_callback(self):
        if bool(self.__current_file):
            self.driver.delete_files_callback(self.__current_file)

    def _button_wrapper_callback(self):
        open_file(self.__current_file)
