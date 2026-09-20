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


class _FfModuleStatus(ModuleStatus):
    """A base class that implements common logic for reading FFmpeg/FFprobe version output."""

    _FFMPEG = "ffmpeg"
    _FFPROBE = "ffprobe"

    @classmethod
    def ff_version(cls, command: str):
        ff_cmd = cls._which(command)
        if ff_cmd:
            out = silent_run([ff_cmd, "-version"], shell=False, capture_output=True, text=True)
            if out.returncode == 0:
                with contextlib.suppress(Exception):
                    return str(out.stdout).split(" ")[2]


class FfmpegStatus(_FfModuleStatus):
    """Class for getting the location and version of FFmpeg, if it exists."""

    @override
    @classmethod
    def which(cls):
        return cls._which(cls._FFMPEG)

    @override
    @classmethod
    def _version(cls):
        return cls.ff_version(cls._FFMPEG)


class FfprobeStatus(_FfModuleStatus):
    """Class for getting the location and version of FFprobe, if it exists."""

    @override
    @classmethod
    def which(cls):
        return cls._which(cls._FFPROBE)

    @override
    @classmethod
    def _version(cls):
        return cls.ff_version(cls._FFPROBE)
