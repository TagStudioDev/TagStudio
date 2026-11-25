# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import re
from functools import lru_cache

import requests
import semver
import structlog

logger = structlog.get_logger(__name__)

_UPDATE_CHECK_TIMEOUT = 10


@lru_cache(maxsize=1)
def get_most_recent_release_version() -> str | None:
    """Get the version of the most recent GitHub release and cache the result."""
    logger.info("[UpdateCheck] Checking for updates...")

    try:
        resp = requests.get(
            "https://api.github.com/repos/TagStudioDev/TagStudio/releases/latest",
            timeout=_UPDATE_CHECK_TIMEOUT,
        )
    except Exception as e:
        logger.error("[UpdateCheck] Error getting most recent GitHub release", error=e)
        return None

    if resp.status_code != 200:
        logger.error(
            "[UpdateCheck] Error getting most recent GitHub release", status_code=resp.status_code
        )
        return None

    data = resp.json()
    tag: str = data["tag_name"]
    if not tag.startswith("v"):
        logger.error("[UpdateCheck] Unexpected git tag format", tag=tag)
        return None

    version = tag[1:]
    # the assertion does not allow for prerelease/build,
    # because the latest release should never have them
    if re.match(r"^\d+\.\d+\.\d+$", version) is None:
        logger.error("[UpdateCheck] Invalid version format", version=version)
        return None

    logger.info(f"[UpdateCheck] Check complete. Most recent GitHub release: v{version}")
    return version


def is_version_outdated(current: str, latest: str) -> bool:
    vcur = semver.Version.parse(current)
    vlat = semver.Version.parse(latest)
    assert vlat.prerelease is None and vlat.build is None

    if vcur.major != vlat.major:
        return vcur.major < vlat.major
    elif vcur.minor != vlat.minor:
        return vcur.minor < vlat.minor
    elif vcur.patch != vlat.patch:
        return vcur.patch < vlat.patch
    else:
        return vcur.prerelease is not None or vcur.build is not None
