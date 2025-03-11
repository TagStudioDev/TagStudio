# Copyright (C) 2022  Karl Kroening (kkroening).
# Licensed under the GPL-3.0 License.
# Vendored from ffmpeg-python and ffmpeg-python PR#790 by amamic1803

import contextlib
import json
import platform
import subprocess
from shutil import which

import ffmpeg
import structlog

from tagstudio.qt.helpers.silent_popen import silent_Popen, silent_run

logger = structlog.get_logger(__name__)

FFMPEG_MACOS_LOCATIONS: list[str] = ["", "/opt/homebrew/bin/", "/usr/local/bin/"]


def _get_ffprobe_location() -> str:
    cmd: str = "ffprobe"
    if platform.system() == "Darwin":
        for loc in FFMPEG_MACOS_LOCATIONS:
            if which(loc + cmd):
                cmd = loc + cmd
                break
    logger.info(
        f"[FFmpeg] Using FFprobe location: {cmd}{' (Found)' if which(cmd) else ' (Not Found)'}"
    )
    return cmd


def _get_ffmpeg_location() -> str:
    cmd: str = "ffmpeg"
    if platform.system() == "Darwin":
        for loc in FFMPEG_MACOS_LOCATIONS:
            if which(loc + cmd):
                cmd = loc + cmd
                break
    logger.info(
        f"[FFmpeg] Using FFmpeg location: {cmd}{' (Found)' if which(cmd) else ' (Not Found)'}"
    )
    return cmd


FFPROBE_CMD = _get_ffprobe_location()
FFMPEG_CMD = _get_ffmpeg_location()


def probe(filename, cmd=FFPROBE_CMD, timeout=None, **kwargs):
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


def version():
    """Checks the version of FFmpeg and FFprobe and returns None if they dont exist."""
    version: dict[str, str | None] = {"ffmpeg": None, "ffprobe": None}

    if which(FFMPEG_CMD):
        ret = silent_run([FFMPEG_CMD, "-version"], shell=False, capture_output=True, text=True)
        if ret.returncode == 0:
            with contextlib.suppress(Exception):
                version["ffmpeg"] = ret.stdout.split(" ")[2]

    if which(FFPROBE_CMD):
        ret = silent_run([FFPROBE_CMD, "-version"], shell=False, capture_output=True, text=True)
        if ret.returncode == 0:
            with contextlib.suppress(Exception):
                version["ffprobe"] = ret.stdout.split(" ")[2]

    return version
