# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""Command-line interface driver for TagStudio."""

from pathlib import Path

import structlog

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.refresh import RefreshTracker

logger = structlog.get_logger(__name__)


class CliDriver:
    """Handles command-line operations without launching the GUI."""

    def __init__(self):
        self.lib = Library()

    def refresh_library(self, library_path: str) -> int:
        """Refresh a library to scan for new files.

        Args:
            library_path: Path to the TagStudio library folder.

        Returns:
            Exit code: 0 for success, 1 for failure.
        """
        path = Path(library_path).expanduser()

        if not path.exists():
            logger.error("Library path does not exist", path=path)
            return 1

        logger.info("Opening library", path=path)
        open_status = self.lib.open_library(path)

        if not open_status.success:
            logger.error(
                "Failed to open library",
                message=open_status.message,
                description=open_status.msg_description,
            )
            return 1

        if open_status.json_migration_req:
            logger.error(
                "Library requires JSON to SQLite migration. "
                "Please open the library in the GUI to complete the migration."
            )
            return 1

        logger.info("Library opened successfully", path=path)

        # Perform the refresh
        logger.info("Starting library refresh")
        tracker = RefreshTracker(self.lib)

        try:
            files_scanned = 0
            new_files_count = 0

            # Refresh the library directory
            for count in tracker.refresh_dir(path):
                files_scanned = count

            new_files_count = tracker.files_count

            # Save newly found files
            for _ in tracker.save_new_files():
                pass

            logger.info(
                "Library refresh completed",
                files_scanned=files_scanned,
                new_files_added=new_files_count,
                message=(
                    f"Refresh complete: scanned {files_scanned} files, "
                    f"added {new_files_count} new entries"
                ),
            )
            return 0

        except Exception as e:
            logger.exception("Error during library refresh", error=str(e))
            return 1

        finally:
            self.lib.close()
