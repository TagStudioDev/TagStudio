# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

import os
import platform
from shutil import which

import structlog

logger = structlog.get_logger(__name__)
user = os.environ.get("USER", None)

# NOTE: macOS does not make its PATH variable available to processes started outside the terminal.
# The following is a list of common directories to search for binaries in.
MACOS_BIN_LOCATIONS: list[str] = [
    "",
    "/opt/homebrew/bin/",
    "/usr/local/bin/",
    f"/etc/profiles/per-user/{user}/bin/",
    "~/.nix-profile/bin/",
]


class ModuleStatus:
    """An abstract base class for module status logic including the binary location and version."""

    _cached_location: str | None = None
    _cached_version: str | None = None

    @classmethod
    def which(cls) -> str | None:
        raise NotImplementedError()

    @classmethod
    def version(cls) -> str | None:
        raise NotImplementedError()

    @staticmethod
    def _which(cmd: str) -> str | None:
        """Internal method for determining the correct location for which().

        Args:
            cmd (str): The process command to search for.
        """
        if platform.system() == "Darwin":
            for loc in MACOS_BIN_LOCATIONS:
                if which(loc + cmd):
                    cmd = loc + cmd
                    break
        return cmd
