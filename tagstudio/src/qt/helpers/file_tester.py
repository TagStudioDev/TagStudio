# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import ffmpeg
from pathlib import Path


def is_readable_video(filepath: Path | str):
    """Test if a video is in a readable format. Examples of unreadable videos
    include files with undetermined codecs and DRM-protected content.

    Args:
        filepath (Path | str):
    """
    probe = ffmpeg.probe(Path(filepath))
    for stream in probe["streams"]:
        if stream.get("codec_tag_string") in [
            "[0][0][0][0]",
            "drma",
            "drms",
            "drmi",
        ]:
            return False
    return True
