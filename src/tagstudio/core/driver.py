# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

import structlog
from PySide6.QtCore import QSettings

from tagstudio.core.constants import TS_FOLDER_NAME
from tagstudio.core.enums import AppCacheItems
from tagstudio.core.library.alchemy.library import OpenLibraryResult
from tagstudio.core.query_lang.file_groups import register_types
from tagstudio.i18n.translations import Translations
from tagstudio.qt.app_settings import AppSettings

logger = structlog.get_logger(__name__)


# TODO: Turn into a BaseDriver class instead of a "Mixin".
class DriverMixin:
    cached_values: QSettings
    # TODO: AppSettings is Qt-specific and should not be in a base driver class.
    settings: AppSettings

    register_types()  # Register all filetypes for the SEARCH context.

    def evaluate_path(self, open_path: str | None) -> OpenLibraryResult:
        """Check if the path of library is valid."""
        library_path: Path | None = None
        if open_path:
            library_path = Path(open_path).expanduser()
            if not library_path.exists():
                logger.error("A TagStudio library at the given path does not exist", path=open_path)
                return OpenLibraryResult(
                    success=False,
                    error_title=Translations["menu.file.missing_library.title"],
                    error_description=Translations.format(
                        "menu.file.missing_library.message", library=open_path
                    ),
                )
        elif self.settings.open_last_loaded_on_startup and self.cached_values.value(
            AppCacheItems.LAST_LIBRARY
        ):
            library_path = Path(str(self.cached_values.value(AppCacheItems.LAST_LIBRARY)))
            if not (library_path / TS_FOLDER_NAME).exists():
                logger.error(
                    "TagStudio folder does not exist.",
                    library_path=library_path,
                    ts_folder=TS_FOLDER_NAME,
                )
                self.cached_values.setValue(AppCacheItems.LAST_LIBRARY, "")
                # dont consider this a fatal error, just skip opening the library
                library_path = None

        return OpenLibraryResult(
            success=True,
            library_path=library_path,
        )
