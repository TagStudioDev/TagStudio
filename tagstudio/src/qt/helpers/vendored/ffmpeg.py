# Copyright (C) 2022  Karl Kroening (kkroening).
# Licensed under the GPL-3.0 License.
# Vendored from ffmpeg-python and ffmpeg-python PR#790 by amamic1803

import json
import platform
import shutil
import subprocess

import ffmpeg
import structlog
from src.qt.helpers.silent_popen import silent_Popen

logger = structlog.get_logger(__name__)

FFMPEG_MACOS_LOCATIONS: list[str] = ["", "/opt/homebrew/bin/", "/usr/local/bin/"]


def _get_ffprobe_location() -> str:
    cmd: str = "ffprobe"
    if platform.system() == "Darwin":
        for loc in FFMPEG_MACOS_LOCATIONS:
            if shutil.which(loc + cmd):
                cmd = loc + cmd
                break
    logger.info(f"[FFMPEG] Using FFprobe location: {cmd}")
    return cmd


def _get_ffmpeg_location() -> str:
    cmd: str = "ffmpeg"
    if platform.system() == "Darwin":
        for loc in FFMPEG_MACOS_LOCATIONS:
            if shutil.which(loc + cmd):
                cmd = loc + cmd
                break
    logger.info(f"[FFMPEG] Using FFmpeg location: {cmd}")
    return cmd


FFPROBE_CMD = _get_ffprobe_location()
FFMPEG_CMD = _get_ffmpeg_location()


def _probe(filename, cmd=FFPROBE_CMD, timeout=None, **kwargs):
    """Run ffprobe on the specified file and return a JSON representation of the output.

    Raises:
        :class:`ffmpeg.Error`: if ffprobe returns a non-zero exit code,
            an :class:`Error` is returned with a generic error message.
            The stderr output can be retrieved by accessing the
            ``stderr`` property of the exception.
    """
    args = [cmd, "-show_format", "-show_streams", "-of", "json"]
    args += ffmpeg._utils.convert_kwargs_to_cmd_line_args(kwargs)
    args += [filename]

    # PATCHED
    p = silent_Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    communicate_kwargs = {}
    if timeout is not None:
        communicate_kwargs["timeout"] = timeout
    out, err = p.communicate(**communicate_kwargs)
    if p.returncode != 0:
        raise ffmpeg.Error("ffprobe", out, err)
    return json.loads(out.decode("utf-8"))
