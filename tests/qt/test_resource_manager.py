# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import structlog

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.resource_manager import ResourceManager

logger = structlog.get_logger()


def test_get():
    rm = ResourceManager()

    for res in rm._map:  # pyright: ignore[reportPrivateUsage]
        assert rm.get(res), f"Could not get resource '{res}'"
        assert unwrap(rm.get_path(res)).exists(), f"Filepath for resource '{res}' does not exist"
