from pathlib import Path

import structlog
from PySide6.QtCore import QSettings

from tagstudio.core.constants import TS_FOLDER_NAME
from tagstudio.core.enums import SettingItems
from tagstudio.core.global_settings import GlobalSettings
from tagstudio.core.library.alchemy.library import LibraryStatus

logger = structlog.get_logger(__name__)


class DriverMixin:
    cached_values: QSettings
    settings: GlobalSettings

    def evaluate_path(self, open_path: str | None) -> LibraryStatus:
        """Check if the path of library is valid."""
        library_path: Path | None = None
        if open_path:
            library_path = Path(open_path).expanduser()
            if not library_path.exists():
                logger.error("Path does not exist.", open_path=open_path)
                return LibraryStatus(success=False, message="Path does not exist.")
        elif self.settings.open_last_loaded_on_startup and self.cached_values.value(
            SettingItems.LAST_LIBRARY
        ):
            library_path = Path(str(self.cached_values.value(SettingItems.LAST_LIBRARY)))
            if not (library_path / TS_FOLDER_NAME).exists():
                logger.error(
                    "TagStudio folder does not exist.",
                    library_path=library_path,
                    ts_folder=TS_FOLDER_NAME,
                )
                self.cached_values.setValue(SettingItems.LAST_LIBRARY, "")
                # dont consider this a fatal error, just skip opening the library
                library_path = None

        return LibraryStatus(
            success=True,
            library_path=library_path,
        )
