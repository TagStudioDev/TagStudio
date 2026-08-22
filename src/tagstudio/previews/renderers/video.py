# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from pathlib import Path
from typing import override

import cv2
import structlog
from cv2.typing import MatLike
from PIL import UnidentifiedImageError
from PIL.Image import DecompressionBombError, Image, fromarray

from tagstudio.core.enums import Theme
from tagstudio.previews.base_preview import BasePreview
from tagstudio.previews.video_tester import is_readable_video

logger = structlog.get_logger(__name__)


class VideoPreview(BasePreview):
    media_type_name = "video"

    @override
    @classmethod
    def render(
        cls,
        filepath: Path,
        is_small: bool,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image | None:
        return video_thumb(filepath)


def video_thumb(filepath: Path) -> Image | None:
    """Render a thumbnail for a video file.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image | None = None
    frame: MatLike | None = None
    try:
        if is_readable_video(filepath):
            video = cv2.VideoCapture(str(filepath), cv2.CAP_FFMPEG)
            # TODO: Move this check to is_readable_video()
            if video.get(cv2.CAP_PROP_FRAME_COUNT) <= 0:
                raise cv2.error("File is invalid or has 0 frames")
            video.set(
                cv2.CAP_PROP_POS_FRAMES,
                (video.get(cv2.CAP_PROP_FRAME_COUNT) // 2),
            )
            # NOTE: Depending on the video format, compression, and
            # frame count, seeking halfway does not work and the thumb
            # must be pulled from the earliest available frame.
            max_frame_seek: int = 10
            for i in range(
                0,
                min(max_frame_seek, math.floor(video.get(cv2.CAP_PROP_FRAME_COUNT))),
            ):
                success, frame = video.read()
                if not success:
                    video.set(cv2.CAP_PROP_POS_FRAMES, i)
                else:
                    break
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                im = fromarray(frame)
    except (
        UnidentifiedImageError,
        cv2.error,
        DecompressionBombError,
        OSError,
    ) as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im
