# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""The core classes and methods of TagStudio."""

import re
from functools import lru_cache

import requests
import structlog

from tagstudio.core.library.alchemy.library import Library

logger = structlog.get_logger(__name__)

MOST_RECENT_RELEASE_VERSION: str | None = None


class TagStudioCore:
    def __init__(self):
        self.lib: Library = Library()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_most_recent_release_version() -> str:
        """Get the version of the most recent Github release."""
        resp = requests.get("https://api.github.com/repos/TagStudioDev/TagStudio/releases/latest")
        assert resp.status_code == 200, "Could not fetch information on latest release."

        data = resp.json()
        tag: str = data["tag_name"]
        assert tag.startswith("v")

        version = tag[1:]
        # the assert does not allow for prerelease/build,
        # because the latest release should never have them
        assert re.match(r"^\d+\.\d+\.\d+$", version) is not None, "Invalid version format."

        return version
