# SPDX-FileCopyrightText: (c) 2022  Karl Kroening (kkroening)
# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only
# Vendored from ffmpeg-python and ffmpeg-python PR#790 by amamic1803


import json
import subprocess
from pathlib import Path

import ffmpeg
import structlog

from tagstudio.core.utils.ffmpeg_status import FfprobeStatus
from tagstudio.core.utils.silent_subprocess import (
    silent_popen,  # pyright: ignore[reportUnknownVariableType]
)

logger = structlog.get_logger(__name__)


def probe(filename: Path | str, timeout: int | None = None, **kwargs: ...):
    """Run ffprobe on the specified file and return a JSON representation of the output.

    Raises:
        Error: If ffprobe returns a non-zero exit code, an Error is raised
            with a generic error message. The stderr output can be retrieved
            by accessing the `stderr` property of the exception.
    """
    ffprobe_cmd: str | None = FfprobeStatus.which()
    if not ffprobe_cmd:
        return
    args: list[str] = [ffprobe_cmd, "-show_format", "-show_streams", "-of", "json"]
    args += ffmpeg._utils.convert_kwargs_to_cmd_line_args(kwargs)  # pyright: ignore
    args += [filename]  # pyright: ignore

    # PATCHED
    p = silent_popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    communicate_kwargs = {}
    if timeout is not None:
        communicate_kwargs["timeout"] = timeout
    out, err = p.communicate(**communicate_kwargs)
    if p.returncode != 0:
        raise ffmpeg.Error("ffprobe", out, err)
    return json.loads(out.decode("utf-8"))
