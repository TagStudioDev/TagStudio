from pathlib import Path

import structlog
from PySide6.QtCore import QSettings
from src.core.enums import SettingItems
from src.core.library.alchemy.library import LibraryStatus

logger = structlog.get_logger(__name__)


class DriverMixin:
    settings: QSettings

    def evaluate_path(self, open_path: str | None) -> LibraryStatus:
        """Check if the path of library is valid."""
        storage_path: Path | None = None
        if open_path:
            storage_path = Path(open_path)
            if not storage_path.exists():
                logger.error("Path does not exist.", open_path=open_path)
                return LibraryStatus(success=False, message="Path does not exist.")
        elif self.settings.value(
            SettingItems.START_LOAD_LAST, defaultValue=True, type=bool
        ) and self.settings.value(SettingItems.LAST_LIBRARY):
            storage_path = Path(str(self.settings.value(SettingItems.LAST_LIBRARY)))
            if not storage_path.exists():
                logger.error(
                    "TagStudio folder does not exist.",
                    storage_path=storage_path,
                )
                self.settings.setValue(SettingItems.LAST_LIBRARY, "")
                # dont consider this a fatal error, just skip opening the library
                storage_path = None

        return LibraryStatus(
            success=True,
            storage_path=storage_path,
        )
