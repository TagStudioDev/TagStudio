# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

import structlog

from tagstudio.core.constants import TS_FOLDER_NAME
from tagstudio.core.library.alchemy.library import OpenLibraryResult
from tagstudio.i18n.translations import Translations

logger = structlog.get_logger(__name__)


class BaseDriver:
    """A base class for TagStudio frontend drivers."""

    def verify_library_path(
        self, path: str | Path, allow_creation: bool = True
    ) -> OpenLibraryResult:
        """Verify that a given library path can be opened.

        Args:
            path (str | Path): The library path to verify.
            allow_creation (bool): Whether a folder without an existing library is valid, since a
                new library can be created there. Not desirable for startup behavior.
        """
        library_path = Path(path).expanduser().absolute()
        library_exists = (library_path / TS_FOLDER_NAME).is_dir()
        if not (library_exists or (allow_creation and library_path.is_dir())):
            logger.error(
                "[Library] No valid library at path",
                path=library_path,
                allow_creation=allow_creation,
            )
            return OpenLibraryResult(
                success=False,
                library_path=library_path,
                error_title=Translations["menu.file.missing_library.title"],
                error_description=Translations.format(
                    "menu.file.missing_library.message", library=library_path
                ),
            )
        return OpenLibraryResult(success=True, library_path=library_path)
