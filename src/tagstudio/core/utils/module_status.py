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
# TODO: Use a library for XDG compliance
_MACOS_BIN_LOCATIONS: list[str] = [
    "",  # Equates to PATH itself
    # User level
    "~/.local/share/bin/",  # XDG-compliant user-created bin
    "~/.local/bin/",  # Fallback user-created bin
    "~/.local/state/nix/profile/bin/",  # XDG-compliant home Nix bin
    "~/.nix-profile/bin/",  # Fallback home Nix bin
    # System level
    f"/etc/profiles/per-user/{user}/bin/",  # Per-user Nix bin
    "/nix/var/nix/profiles/default/bin/",  # Inherited Nix bin
    "/opt/homebrew/bin/",  # Homebrew bin
    "/usr/local/bin/",  # Administrator-configured bin
    "/usr/bin/",  # System bin
    "/bin/",  # Core system bin
]


class ModuleStatus:
    """An abstract base class for module status logic including the binary location and version."""

    __cached_location: str | None = None
    __cached_version: str | None = None

    @classmethod
    def which(cls) -> str | None:
        raise NotImplementedError()

    @classmethod
    def _cache_location(cls) -> str | None:
        raise NotImplementedError()

    @classmethod
    def version(cls) -> str | None:
        if cls.__cached_version is None:
            cls.__cached_version = cls._version()
        return cls.__cached_version

    @classmethod
    def _version(cls) -> str | None:
        raise NotImplementedError()

    @classmethod
    def _which(cls, cmd: str) -> str | None:
        """Internal method for determining the correct location for which().

        Args:
            cmd (str): The process command to search for.
        """
        if cls.__cached_location:
            return cls.__cached_location

        if platform.system() == "Darwin":
            for loc in _MACOS_BIN_LOCATIONS:
                full_command = which(loc + cmd)
                if full_command:
                    cls.__cached_location = full_command
                    return full_command

        cls.__cached_location = which(cmd)
        return cls.__cached_location
