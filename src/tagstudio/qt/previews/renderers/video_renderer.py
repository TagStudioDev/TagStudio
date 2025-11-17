import math
from pathlib import Path

import cv2
import structlog
from cv2.typing import MatLike
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError

from tagstudio.qt.helpers.file_tester import is_readable_video
from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer

logger = structlog.get_logger(__name__)


class VideoRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(path: Path, extension: str) -> Image.Image | None:
        """Render a thumbnail for a video file.

        Args:
            path (Path): The path of the file.
            extension (str): The file extension.
        """
        try:
            if is_readable_video(path):
                video = cv2.VideoCapture(str(path), cv2.CAP_FFMPEG)

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
                frame: MatLike | None = None

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
                    return Image.fromarray(frame)
        except (
            UnidentifiedImageError,
            cv2.error,
            DecompressionBombError,
            OSError,
        ) as e:
            logger.error("[VideoRenderer] Couldn't render thumbnail", path=path, error=e)

        return None
