from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaCategories, MediaType
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

    def display_file(self, filepath: Path) -> dict[str, int]:
        """Render a single file preview."""
        self.__current_file = filepath

        ext = filepath.suffix.lower()

        # Video
        if MediaCategories.VIDEO_TYPES.contains(ext, mime_fallback=True) and is_readable_video(
            filepath
        ):
            return self._display_file(filepath, MediaType.VIDEO)
        # Audio
        elif MediaCategories.AUDIO_TYPES.contains(ext, mime_fallback=True):
            return self._display_file(filepath, MediaType.AUDIO)
        # Animated Images
        elif MediaCategories.IMAGE_ANIMATED_TYPES.contains(ext, mime_fallback=True):
            return self._display_file(filepath, MediaType.IMAGE_ANIMATED)
        # Other Types (Including Images)
        else:
            return self._display_file(filepath, MediaType.IMAGE)

    def _open_file_action_callback(self):
        open_file(self.__current_file)

    def _open_explorer_action_callback(self):
        open_file(self.__current_file, file_manager=True)

    def _delete_action_callback(self):
        if bool(self.__current_file):
            self.driver.delete_files_callback(self.__current_file)

    def _button_wrapper_callback(self):
        open_file(self.__current_file)
