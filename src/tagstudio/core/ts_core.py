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
    def get_most_recent_release_version() -> str | None:
        """Get the version of the most recent GitHub release."""
        try:
            resp = requests.get(
                "https://api.github.com/repos/TagStudioDev/TagStudio/releases/latest"
            )
        except Exception as e:
            logger.error("Error getting most recent GitHub release.", error=e)
            return None

        if resp.status_code != 200:
            logger.error("Error getting most recent GitHub release.", status_code=resp.status_code)
            return None

        data = resp.json()
        tag: str = data["tag_name"]
        if not tag.startswith("v"):
            logger.error("Unexpected tag format.", tag=tag)
            return None

        version = tag[1:]
        # the assertion does not allow for prerelease/build,
        # because the latest release should never have them
        if re.match(r"^\d+\.\d+\.\d+$", version) is None:
            logger.error("Invalid version format.", version=version)
            return None

        return version
