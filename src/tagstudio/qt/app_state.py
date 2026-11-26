# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

import structlog
from platformdirs import user_state_path
from pydantic import Field
from PySide6.QtCore import QSettings

from tagstudio.core.utils.data_file import BaseDataFile

logger = structlog.get_logger(__name__)

DEFAULT_APP_STATE_PATH = user_state_path("TagStudio", appauthor=False) / "app_state.json"
_LEGACY_CACHE_PATH = Path(
    QSettings(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, "TagStudio", "TagStudio"
    ).fileName()
)
_RECENT_LIBRARIES_LIMIT = 10


class AppState(BaseDataFile):
    """Application state file for TagStudio."""

    last_library: Path | None = None
    recent_libraries: list[Path] = Field(default_factory=list)
    dismissed_update: str | None = None
    last_version_opened: str | None = None

    def add_recent_library(self, library_dir: Path) -> None:
        """Add or move a library to the front of the recent libraries list."""
        older_libraries = [library for library in self.recent_libraries if library != library_dir]
        self.recent_libraries = [library_dir, *older_libraries][:_RECENT_LIBRARIES_LIMIT]


def migrate_legacy_cache(
    legacy_path: Path = _LEGACY_CACHE_PATH, path: Path = DEFAULT_APP_STATE_PATH
) -> None:
    """Convert the legacy TagStudio.ini file to app_state.json."""
    if path.exists() or not legacy_path.exists():
        return
    cache = QSettings(str(legacy_path), QSettings.Format.IniFormat)
    state = AppState(path=path)

    last_library = cache.value("last_library")
    state.last_library = Path(str(last_library)) if last_library else None
    cache.beginGroup("libs_list")
    timestamps = sorted(cache.allKeys(), reverse=True)
    state.recent_libraries = [Path(str(cache.value(timestamp))) for timestamp in timestamps]
    cache.endGroup()
    dismissed_update = cache.value("dismissed_update")
    state.dismissed_update = str(dismissed_update) if dismissed_update else None
    last_version_opened = cache.value("last_version_opened")
    state.last_version_opened = str(last_version_opened) if last_version_opened else None

    state.save()
    if not path.exists():
        return
    try:
        legacy_path.unlink()
    except OSError as error:
        logger.warning(
            "[AppState] Couldn't delete legacy cache file", legacy_path=legacy_path, error=error
        )
    logger.info("[AppState] Converted legacy cache file", legacy_path=legacy_path, path=path)
