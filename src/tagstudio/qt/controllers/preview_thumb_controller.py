# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import io
import time
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import ffmpeg
import rawpy
import structlog
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import QSize
from PySide6.QtGui import QMovie

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaCategories
from tagstudio.qt.helpers.file_tester import is_readable_video
from tagstudio.qt.mixed.file_attributes import FileAttributeData
from tagstudio.qt.utils.file_opener import open_file
from tagstudio.qt.views.preview_thumb_view import PreviewThumbView

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)
Image.MAX_IMAGE_PIXELS = None


class PreviewThumb(PreviewThumbView):
    __current_file: Path

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__(library, driver)

        self.__driver: QtDriver = driver

    def __get_image_stats(self, filepath: Path) -> FileAttributeData:
        """Get width and height of an image as dict."""
        stats = FileAttributeData()
        ext = filepath.suffix.lower()

        if filepath.is_dir():
            pass
        elif MediaCategories.IMAGE_RAW_TYPES.contains(ext, mime_fallback=True):
            try:
                with rawpy.imread(str(filepath)) as raw:
                    rgb = raw.postprocess()
                    image = Image.new("L", (rgb.shape[1], rgb.shape[0]), color="black")
                    stats.width = image.width
                    stats.height = image.height
            except (
                rawpy._rawpy._rawpy.LibRawIOError,  # pyright: ignore[reportAttributeAccessIssue]
                rawpy._rawpy.LibRawFileUnsupportedError,  # pyright: ignore[reportAttributeAccessIssue]
                FileNotFoundError,
            ):
                pass
        elif MediaCategories.IMAGE_RASTER_TYPES.contains(ext, mime_fallback=True):
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
        elif MediaCategories.IMAGE_VECTOR_TYPES.contains(ext, mime_fallback=True):
            pass  # TODO

        return stats

    @staticmethod
    def normalize_formats_to_exts(formats: Iterable[str]) -> list[str]:
        out = []
        for format in formats:
            if not isinstance(format, str):
                logger.error(
                    "passed non-string to `normalize_formats_to_exts` skipping format",
                    item=format,
                )
                continue

            format = format.lower()
            if not format.startswith("."):
                format = "." + format

            out.append(format)

        return out

    def should_convert(self, ext: str, format_exts: Iterable[str]) -> bool:
        if ext in self.normalize_formats_to_exts(
            [b.data().decode("utf-8") for b in QMovie.supportedFormats()]
        ):
            return False

        return ext in self.normalize_formats_to_exts(format_exts)

    def __get_gif_data(self, filepath: Path) -> tuple[bytes, tuple[int, int]] | None:
        """Loads an animated image and returns gif data and size, if successful."""
        ext = filepath.suffix.lower()
        ext_mapping = {
            ".apng": ".png",
        }
        ext = ext_mapping.get(ext, ext)

        try:
            image: Image.Image = Image.open(filepath)

            pillow_converts = self.normalize_formats_to_exts(Image.SAVE_ALL.keys())

            if self.should_convert(ext, [".jxl"]):
                image.close()

                start = time.perf_counter_ns()
                ffprobe = ffmpeg.probe(filepath)

                if ffprobe.get("format", {}).get("format_name", "") != "jpegxl_anim":
                    return None

                probe_time = f"{(time.perf_counter_ns() - start) / 1_000_000} ms"

                start = time.perf_counter_ns()

                out, _ = (
                    ffmpeg.input(filepath)
                    .output(
                        "pipe:",
                        format="webp",
                        **{
                            "lossless": 1,
                            "compression_level": 0,
                            "loop": 0,
                        },
                    )
                    .global_args("-hide_banner", "-loglevel", "error")
                    .run(capture_stdout=True)
                )

                logger.debug(
                    f"[PreviewThumb] Coversion has taken {
                        (time.perf_counter_ns() - start) / 1_000_000
                    } ms",
                    ext=ext,
                    ffprobe_time=probe_time,
                )

                return (out, (image.width, image.height))

            elif self.should_convert(ext, pillow_converts):
                if getattr(image, "n_frames", -1) <= 1:
                    return None

                image_bytes_io = io.BytesIO()
                start = time.perf_counter_ns()
                image.save(
                    image_bytes_io,
                    "WEBP",
                    lossless=True,
                    save_all=True,
                    loop=0,
                )
                logger.debug(
                    f"[PreviewThumb] Coversion has taken {
                        (time.perf_counter_ns() - start) / 1_000_000
                    } ms",
                    ext=ext,
                )

                image.close()
                image_bytes_io.seek(0)
                return (image_bytes_io.read(), (image.width, image.height))

            elif ext in self.normalize_formats_to_exts(
                [b.data().decode("utf-8") for b in QMovie.supportedFormats()]
            ):
                image.close()
                with open(filepath, "rb") as f:
                    return (f.read(), (image.width, image.height))
            else:
                return None

        except (UnidentifiedImageError, FileNotFoundError) as e:
            logger.error("[PreviewThumb] Could not load animated image", filepath=filepath, error=e)
            return None

    def __get_video_res(self, filepath: str) -> tuple[bool, QSize]:
        video = cv2.VideoCapture(filepath, cv2.CAP_FFMPEG)
        success, frame = video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        return (success, QSize(image.width, image.height))

    def display_file(self, filepath: Path) -> FileAttributeData:
        """Render a single file preview."""
        self.__current_file = filepath

        ext = filepath.suffix.lower()

        # Video
        if MediaCategories.VIDEO_TYPES.contains(ext, mime_fallback=True) and is_readable_video(
            filepath
        ):
            size: QSize | None = None
            try:
                success, size = self.__get_video_res(str(filepath))
                if not success:
                    size = None
            except cv2.error as e:
                logger.error("[PreviewThumb] Could not play video", filepath=filepath, error=e)

            return self._display_video(filepath, size)
        # Audio
        elif MediaCategories.AUDIO_TYPES.contains(ext, mime_fallback=True):
            return self._display_audio(filepath)
        # Animated Images
        elif MediaCategories.IMAGE_ANIMATED_TYPES.contains(ext, mime_fallback=True):
            if (ret := self.__get_gif_data(filepath)) and (
                stats := self._display_gif(ret[0], ret[1])
            ) is not None:
                return stats
            else:
                self._display_image(filepath)
                return self.__get_image_stats(filepath)
        # Other Types (Including Images)
        else:
            self._display_image(filepath)
            return self.__get_image_stats(filepath)

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
