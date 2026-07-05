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


class RipgrepStatus(ModuleStatus):
    """Class for getting the location and version of ripgrep, if it exists."""

    @override
    @classmethod
    def which(cls):
        return cls._which("rg")

    @override
    @classmethod
    def _version(cls):
        ripgrep_cmd = cls.which()
        if ripgrep_cmd:
            out = silent_run([ripgrep_cmd, "-V"], shell=False, capture_output=True, text=True)
            if out.returncode == 0:
                with contextlib.suppress(Exception):
                    return str(out.stdout).split(" ")[1].rstrip("\n")
