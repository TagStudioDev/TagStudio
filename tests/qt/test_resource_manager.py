# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.resource_manager import ResourceManager

logger = structlog.get_logger()


def test_get():
    rm = ResourceManager()

    for res in rm._map:
        assert rm.get(res), f"Could not get resource '{res}'"
        assert unwrap(rm.get_path(res)).exists(), f"Filepath for resource '{res}' does not exist"
