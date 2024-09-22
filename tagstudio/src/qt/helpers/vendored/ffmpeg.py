# Copyright (C) 2022  Karl Kroening (kkroening).
# Licensed under the GPL-3.0 License.
# Vendored from ffmpeg-python and ffmpeg-python PR#790 by amamic1803

import json
import subprocess

import ffmpeg
from src.qt.helpers.silent_popen import promptless_Popen


def _probe(filename, cmd="ffprobe", timeout=None, **kwargs):
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
    p = promptless_Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    communicate_kwargs = {}
    if timeout is not None:
        communicate_kwargs["timeout"] = timeout
    out, err = p.communicate(**communicate_kwargs)
    if p.returncode != 0:
        raise ffmpeg.Error("ffprobe", out, err)
    return json.loads(out.decode("utf-8"))
