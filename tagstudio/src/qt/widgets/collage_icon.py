# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import math
from pathlib import Path

import cv2
import structlog
from PIL import Image, ImageChops, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import (
    QObject,
    Signal,
)
from src.core.library import Library
from src.core.media_types import MediaCategories
from src.qt.helpers.file_tester import is_readable_video

logger = structlog.get_logger(__name__)


class CollageIconRenderer(QObject):
    rendered = Signal(Image.Image)
    done = Signal()

    def __init__(self, library: Library):
        QObject.__init__(self)
        self.lib = library

    def render(
        self,
        entry_id,
        size: tuple[int, int],
        data_tint_mode,
        data_only_mode,
        keep_aspect,
    ):
        entry = self.lib.get_entry(entry_id)
        filepath = self.lib.library_dir / entry.path
        color: str = ""

        try:
            if data_tint_mode or data_only_mode:
                color = "#28bb48" if entry.tags else "#e22c3c"

                if data_only_mode:
                    pic = Image.new("RGB", size, color)
                    # collage.paste(pic, (y*thumb_size, x*thumb_size))
                    self.rendered.emit(pic)
            if not data_only_mode:
                logger.info(
                    "Combining icons",
                    entry=entry,
                    color=self.get_file_color(filepath.suffix.lower()),
                )

                ext: str = filepath.suffix.lower()
                if MediaCategories.is_ext_in_category(ext, MediaCategories.IMAGE_TYPES):
                    try:
                        with Image.open(str(self.lib.library_dir / entry.path)) as pic:
                            if keep_aspect:
                                pic.thumbnail(size)
                            else:
                                pic = pic.resize(size)
                            if data_tint_mode and color:
                                pic = pic.convert(mode="RGB")
                                pic = ImageChops.hard_light(pic, Image.new("RGB", size, color))
                            self.rendered.emit(pic)
                    except DecompressionBombError as e:
                        logger.info(f"[ERROR] One of the images was too big ({e})")
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.VIDEO_TYPES
                ) and is_readable_video(filepath):
                    video = cv2.VideoCapture(str(filepath), cv2.CAP_FFMPEG)
                    video.set(
                        cv2.CAP_PROP_POS_FRAMES,
                        (video.get(cv2.CAP_PROP_FRAME_COUNT) // 2),
                    )
                    success, frame = video.read()
                    # NOTE: Depending on the video format, compression, and
                    # frame count, seeking halfway does not work and the thumb
                    # must be pulled from the earliest available frame.
                    max_frame_seek: int = 10
                    for i in range(
                        0,
                        min(
                            max_frame_seek,
                            math.floor(video.get(cv2.CAP_PROP_FRAME_COUNT)),
                        ),
                    ):
                        success, frame = video.read()
                        if not success:
                            video.set(cv2.CAP_PROP_POS_FRAMES, i)
                        else:
                            break
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    with Image.fromarray(frame, mode="RGB") as pic:
                        if keep_aspect:
                            pic.thumbnail(size)
                        else:
                            pic = pic.resize(size)
                        if data_tint_mode and color:
                            pic = ImageChops.hard_light(pic, Image.new("RGB", size, color))
                        self.rendered.emit(pic)
        except (UnidentifiedImageError, FileNotFoundError):
            logger.error("Couldn't read entry", entry=entry.path)
            with Image.open(
                str(Path(__file__).parents[2] / "resources/qt/images/thumb_broken_512.png")
            ) as pic:
                pic.thumbnail(size)
                if data_tint_mode and color:
                    pic = pic.convert(mode="RGB")
                    pic = ImageChops.hard_light(pic, Image.new("RGB", size, color))
                # collage.paste(pic, (y*thumb_size, x*thumb_size))
                self.rendered.emit(pic)
        except KeyboardInterrupt:
            logger.info("Collage operation cancelled.")
        except Exception:
            logger.exception("render failed", entry=entry.path)

        self.done.emit()

    def get_file_color(self, ext: str):
        if ext.lower() == "gif":
            return "\033[93m"
        if MediaCategories.is_ext_in_category(ext, MediaCategories.IMAGE_TYPES):
            return "\033[37m"
        elif MediaCategories.is_ext_in_category(ext, MediaCategories.VIDEO_TYPES):
            return "\033[96m"
        elif MediaCategories.is_ext_in_category(ext, MediaCategories.PLAINTEXT_TYPES):
            return "\033[92m"
        else:
            return "\033[97m"
