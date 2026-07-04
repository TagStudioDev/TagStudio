# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import contextlib
from typing import override

import structlog

from tagstudio.core.utils.module_status import ModuleStatus
from tagstudio.core.utils.silent_subprocess import (
    silent_run,  # pyright: ignore[reportUnknownVariableType]
)

logger = structlog.get_logger(__name__)


class FfmpegStatus(ModuleStatus):
    """Class for getting the location and version of FFmpeg, if it exists."""

    @override
    @classmethod
    def which(cls):
        if cls._cached_location:
            return cls._cached_location

        cls._cached_location = cls._which("ffmpeg")
        return cls._cached_location

    @override
    @classmethod
    def version(cls):
        if cls._cached_version:
            return cls._cached_version

        ffmpeg_cmd = cls._which("ffmpeg")
        if ffmpeg_cmd:
            out = silent_run([ffmpeg_cmd, "-version"], shell=False, capture_output=True, text=True)
            if out.returncode == 0:
                with contextlib.suppress(Exception):
                    cls._cached_version = str(out.stdout).split(" ")[2]
                    return cls._cached_version


class FfprobeStatus(ModuleStatus):
    """Class for getting the location and version of FFprobe, if it exists."""

    @override
    @classmethod
    def which(cls):
        if cls._cached_location:
            return cls._cached_location

        cls._cached_location = cls._which("ffprobe")
        return cls._cached_location

    @override
    @classmethod
    def version(cls):
        if cls._cached_version:
            return cls._cached_version

        ffmpeg_cmd = cls._which("ffprobe")
        if ffmpeg_cmd:
            out = silent_run([ffmpeg_cmd, "-version"], shell=False, capture_output=True, text=True)
            if out.returncode == 0:
                with contextlib.suppress(Exception):
                    cls._cached_version = str(out.stdout).split(" ")[2]
                    return cls._cached_version
