# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import os
import traceback
from pathlib import Path

import cv2
from PIL import Image, ImageChops, UnidentifiedImageError
from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
    QRunnable,
    Qt,
    QThreadPool,
    QSize,
    QEvent,
    QTimer,
    QSettings,
)

from src.core.library import Library
from src.core.ts_core import DOC_TYPES, VIDEO_TYPES, IMAGE_TYPES


ERROR = f"[ERROR]"
WARNING = f"[WARNING]"
INFO = f"[INFO]"


logging.basicConfig(format="%(message)s", level=logging.INFO)


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
        filepath = os.path.normpath(
            f"{self.lib.library_dir}/{entry.path}/{entry.filename}"
        )
        file_type = os.path.splitext(filepath)[1].lower()[1:]
        color: str = ""

        try:
            if data_tint_mode or data_only_mode:
                color = "#000000"  # Black (Default)

                if entry.fields:
                    has_any_tags: bool = False
                    has_content_tags: bool = False
                    has_meta_tags: bool = False
                    for field in entry.fields:
                        if self.lib.get_field_attr(field, "type") == "tag_box":
                            if self.lib.get_field_attr(field, "content"):
                                has_any_tags = True
                                if self.lib.get_field_attr(field, "id") == 7:
                                    has_content_tags = True
                                elif self.lib.get_field_attr(field, "id") == 8:
                                    has_meta_tags = True
                    if has_content_tags and has_meta_tags:
                        color = "#28bb48"  # Green
                    elif has_any_tags:
                        color = "#ffd63d"  # Yellow
                        # color = '#95e345' # Yellow-Green
                    else:
                        # color = '#fa9a2c' # Yellow-Orange
                        color = "#ed8022"  # Orange
                else:
                    color = "#e22c3c"  # Red

                if data_only_mode:
                    pic: Image = Image.new("RGB", size, color)
                    # collage.paste(pic, (y*thumb_size, x*thumb_size))
                    self.rendered.emit(pic)
            if not data_only_mode:
                logging.info(
                    f"\r{INFO} Combining [ID:{entry_id}/{len(self.lib.entries)}]: {self.get_file_color(file_type)}{entry.path}{os.sep}{entry.filename}\033[0m"
                )
                # sys.stdout.write(f'\r{INFO} Combining [{i+1}/{len(self.lib.entries)}]: {self.get_file_color(file_type)}{entry.path}{os.sep}{entry.filename}{RESET}')
                # sys.stdout.flush()
                if file_type in IMAGE_TYPES:
                    with Image.open(
                        os.path.normpath(
                            f"{self.lib.library_dir}/{entry.path}/{entry.filename}"
                        )
                    ) as pic:
                        if keep_aspect:
                            pic.thumbnail(size)
                        else:
                            pic = pic.resize(size)
                        if data_tint_mode and color:
                            pic = pic.convert(mode="RGB")
                            pic = ImageChops.hard_light(
                                pic, Image.new("RGB", size, color)
                            )
                        # collage.paste(pic, (y*thumb_size, x*thumb_size))
                        self.rendered.emit(pic)
                elif file_type in VIDEO_TYPES:
                    video = cv2.VideoCapture(filepath)
                    video.set(
                        cv2.CAP_PROP_POS_FRAMES,
                        (video.get(cv2.CAP_PROP_FRAME_COUNT) // 2),
                    )
                    success, frame = video.read()
                    if not success:
                        # Depending on the video format, compression, and frame
                        # count, seeking halfway does not work and the thumb
                        # must be pulled from the earliest available frame.
                        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        success, frame = video.read()
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    with Image.fromarray(frame, mode="RGB") as pic:
                        if keep_aspect:
                            pic.thumbnail(size)
                        else:
                            pic = pic.resize(size)
                        if data_tint_mode and color:
                            pic = ImageChops.hard_light(
                                pic, Image.new("RGB", size, color)
                            )
                        # collage.paste(pic, (y*thumb_size, x*thumb_size))
                        self.rendered.emit(pic)
        except (UnidentifiedImageError, FileNotFoundError):
            logging.info(
                f"\n{ERROR} Couldn't read {entry.path}{os.sep}{entry.filename}"
            )
            with Image.open(
                os.path.normpath(
                    f"{Path(__file__).parent.parent.parent}/resources/qt/images/thumb_broken_512.png"
                )
            ) as pic:
                pic.thumbnail(size)
                if data_tint_mode and color:
                    pic = pic.convert(mode="RGB")
                    pic = ImageChops.hard_light(pic, Image.new("RGB", size, color))
                # collage.paste(pic, (y*thumb_size, x*thumb_size))
                self.rendered.emit(pic)
        except KeyboardInterrupt:
            # self.quit(save=False, backup=True)
            run = False
            # clear()
            logging.info("\n")
            logging.info(f"{INFO} Collage operation cancelled.")
            clear_scr = False
        except:
            logging.info(f"{ERROR} {entry.path}{os.sep}{entry.filename}")
            traceback.print_exc()
            logging.info("Continuing...")

        self.done.emit()
        # logging.info('Done!')

    def get_file_color(self, ext: str):
        if ext.lower().replace(".", "", 1) == "gif":
            return "\033[93m"
        if ext.lower().replace(".", "", 1) in IMAGE_TYPES:
            return "\033[37m"
        elif ext.lower().replace(".", "", 1) in VIDEO_TYPES:
            return "\033[96m"
        elif ext.lower().replace(".", "", 1) in DOC_TYPES:
            return "\033[92m"
        else:
            return "\033[97m"
