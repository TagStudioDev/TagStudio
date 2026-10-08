# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from functools import lru_cache
from pathlib import Path
from typing import Any

import ffmpeg
import structlog
from PIL import Image, ImageSequence

from tagstudio.core.media_types import MediaTypes
from tagstudio.core.query_lang.file_groups import SEARCH
from tagstudio.core.utils.stat import get_date_modified
from tagstudio.previews.vendored.probe import probe

logger = structlog.get_logger(__name__)


def probe_file(filepath: Path) -> dict[str, Any] | None:
    """Return ffprobe's output for a file, or `None` if it can't be probed.

    Results are cached by path and date modified timestamp.
    """
    try:
        mod_time = get_date_modified(filepath)
    except OSError:
        return None
    return _cached_probe(filepath, mod_time)


@lru_cache(maxsize=256)
def _cached_probe(filepath: Path, _mod_time: float) -> dict[str, Any] | None:
    try:
        return probe(filepath)
    except ffmpeg.Error:
        return None


def _readable_streams(filepath: Path) -> list[dict[str, Any]]:
    """Return a file's streams, or an empty list if it can't be probed or is DRM-protected."""
    streams: list[dict[str, Any]] = (probe_file(filepath) or {}).get("streams", [])
    if any(stream.get("codec_tag_string") in ["drma", "drms", "drmi"] for stream in streams):
        return []
    return streams


def get_video_stream(filepath: Path) -> dict[str, Any] | None:
    """Return a file's first readable video stream, skipping embedded cover art."""
    return next(
        (
            stream
            for stream in _readable_streams(filepath)
            if stream.get("codec_type") == "video"
            and not stream.get("disposition", {}).get("attached_pic")
        ),
        None,
    )


def has_audio_stream(filepath: Path) -> bool:
    """Return whether a file has a readable audio stream."""
    return any(stream.get("codec_type") == "audio" for stream in _readable_streams(filepath))


def is_readable_video(filepath: Path | str) -> bool:
    """Test if a video is in a readable format and has a picture to display.

    Examples of unreadable videos include files with undetermined codecs, DRM-protected content,
    and audio-only files.

    Args:
        filepath (Path | str): The filepath of the video to check.
    """
    return get_video_stream(Path(filepath)) is not None


def _is_audio_or_video(ext: str) -> bool:
    return MediaTypes.contains("video", ext, SEARCH) or MediaTypes.contains("audio", ext, SEARCH)


def get_animation_duration(image: Image.Image) -> float:
    """Return the total duration of an animated image's frames, in seconds."""
    duration_ms = 0
    for frame in ImageSequence.Iterator(image):
        frame.load()  # NOTE: Some formats only read a frame's duration once it's loaded.
        duration_ms += frame.info.get("duration", 0)
    return duration_ms / 1000


def get_duration(filepath: Path) -> float | None:
    """Return a media file's duration in seconds, or `None` if it doesn't have one.

    Results are cached by path and date modified timestamp.
    """
    try:
        mod_time = get_date_modified(filepath)
    except OSError:
        return None
    return _cached_duration(filepath, mod_time)


@lru_cache(maxsize=1024)
def _cached_duration(filepath: Path, _mod_time: float) -> float | None:
    ext = filepath.suffix.lower()
    try:
        if _is_audio_or_video(ext):
            format_info = (probe_file(filepath) or {}).get("format", {})
            return float(format_info["duration"]) if "duration" in format_info else None
        if MediaTypes.contains("image.animated", ext, SEARCH):
            with Image.open(filepath) as image:
                if getattr(image, "is_animated", False):
                    return get_animation_duration(image)
    except Exception as e:
        logger.error("[MediaProbe] Could not read duration", filepath=filepath, error=e)
    return None
