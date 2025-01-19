from pathlib import Path

import structlog
from src.core.constants import TS_FOLDER_NAME
from src.core.library.alchemy.library import LibraryStatus
from src.core.settings import TSSettings
from src.core.tscacheddata import TSCachedData

logger = structlog.get_logger(__name__)


class DriverMixin:
    settings: TSSettings
    cache: TSCachedData

    def evaluate_path(self, open_path: str | None) -> LibraryStatus:
        """Check if the path of library is valid."""
        library_path: Path | None = None
        if open_path:
            library_path = Path(open_path).expanduser()
            if not library_path.exists():
                logger.error("Path does not exist.", open_path=open_path)
                return LibraryStatus(success=False, message="Path does not exist.")
        elif self.settings.open_last_loaded_on_startup and self.cache.last_library:
            library_path = Path(str(self.cache.last_library))
            if not (library_path / TS_FOLDER_NAME).exists():
                logger.error(
                    "TagStudio folder does not exist.",
                    library_path=library_path,
                    ts_folder=TS_FOLDER_NAME,
                )
                self.cache.last_library = ""
                # dont consider this a fatal error, just skip opening the library
                library_path = None

        return LibraryStatus(
            success=True,
            library_path=library_path,
        )
