# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import os
from pathlib import Path
from typing import TYPE_CHECKING, override

from humanfriendly import format_size
from PySide6 import QtGui

from tagstudio.core.constants import BACKUP_FOLDER_NAME, TS_FOLDER_NAME
from tagstudio.core.library.alchemy.constants import DB_VERSION, DB_VERSION_CURRENT_KEY
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.translations import Translations
from tagstudio.qt.view.widgets.library_info_window_view import LibraryInfoWindowView

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class LibraryInfoWindow(LibraryInfoWindowView):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__(library, driver)

        # Statistics Buttons
        self.manage_tags_button.clicked.connect(
            self.driver.main_window.menu_bar.tag_manager_action.trigger
        )
        self.manage_colors_button.clicked.connect(
            self.driver.main_window.menu_bar.color_manager_action.trigger
        )

        # Cleanup Buttons
        self.fix_unlinked_entries.clicked.connect(
            self.driver.main_window.menu_bar.fix_unlinked_entries_action.trigger
        )
        self.fix_ignored_files.clicked.connect(
            self.driver.main_window.menu_bar.fix_ignored_files_action.trigger
        )
        self.fix_dupe_files.clicked.connect(
            self.driver.main_window.menu_bar.fix_dupe_files_action.trigger
        )

        # General Buttons
        self.close_button.clicked.connect(lambda: self.close())

    def __update_title(self):
        assert self.lib.library_dir
        title: str = Translations.format(
            "library_info.title", library_dir=self.lib.library_dir.stem
        )
        self.title_label.setText(f"<h2>{title}</h2>")

    def __update_stats(self):
        self.entry_count_label.setText(f"<b>{self.lib.entries_count}</b>")
        self.tag_count_label.setText(f"<b>{len(self.lib.tags)}</b>")
        self.field_count_label.setText(f"<b>{len(self.lib.field_types)}</b>")
        self.namespaces_count_label.setText(f"<b>{len(self.lib.namespaces)}</b>")
        colors_total = 0
        for c in self.lib.tag_color_groups.values():
            colors_total += len(c)
        self.color_count_label.setText(f"<b>{colors_total}</b>")

        self.macros_count_label.setText("<b>1</b>")  # TODO: Implement macros system

    def __update_cleanup(self):
        # TODO: Centralize these counts from their respective modals so they can be used here.
        # self.unlinked_count_label.setText(f"<b>{0}</b>")
        # self.ignored_count_label.setText(f"<b>{0}</b>")
        # self.dupe_files_count_label.setText(f"<b>{0}</b>")

        json_library_text: str = (
            Translations["generic.yes"]
            if self.__is_json_library_present
            else Translations["generic.no"]
        )
        self.legacy_json_status_label.setText(f"<b>{json_library_text}</b>")
        self.backups_count_label.setText(
            f"<b>{self.__backups_count}</b> ({format_size(self.__backups_size)})"
        )

    def __update_version(self):
        version_text: str = f"{self.lib.get_version(DB_VERSION_CURRENT_KEY)} / {DB_VERSION}"
        self.version_label.setText(
            Translations.format("library_info.version", version=version_text)
        )

    @property
    def __is_json_library_present(self):
        json_path = unwrap(self.lib.library_dir) / TS_FOLDER_NAME / Library.JSON_FILENAME
        return json_path.exists()

    @property
    def __backups_count(self):
        backups_path = unwrap(self.lib.library_dir) / TS_FOLDER_NAME / BACKUP_FOLDER_NAME
        return len(os.listdir(backups_path))

    @property
    def __backups_size(self):
        backups_path = unwrap(self.lib.library_dir) / TS_FOLDER_NAME / BACKUP_FOLDER_NAME
        size: int = 0

        for f in backups_path.glob("*"):
            if not f.is_dir() and f.exists():
                size += Path(f).stat().st_size

        return size

    @override
    def showEvent(self, event: QtGui.QShowEvent):  # type: ignore
        self.__update_title()
        self.__update_stats()
        self.__update_cleanup()
        self.__update_version()
