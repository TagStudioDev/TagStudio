# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import ffmpeg
from pathlib import Path

from src.qt.helpers.vendored.ffmpeg import _probe

def is_readable_video(filepath: Path | str):
    """Test if a video is in a readable format. Examples of unreadable videos
    include files with undetermined codecs and DRM-protected content.

    Args:
        filepath (Path | str):
    """
    try:
        probe = _probe(Path(filepath))
        for stream in probe["streams"]:
            # DRM check
            if stream.get("codec_tag_string") in [
                "drma",
                "drms",
                "drmi",
            ]:
                return False
    except ffmpeg.Error:
        return False
    return True
