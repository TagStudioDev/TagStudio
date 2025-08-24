# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING

from PySide6 import QtGui

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.translations import Translations
from tagstudio.qt.view.widgets.library_info_window_view import LibraryInfoWindowView

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class LibraryInfoWindow(LibraryInfoWindowView):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__(library, driver)

        self.manage_tags_button.clicked.connect(
            self.driver.main_window.menu_bar.tag_manager_action.trigger
        )
        self.manage_colors_button.clicked.connect(
            self.driver.main_window.menu_bar.color_manager_action.trigger
        )
        self.close_button.clicked.connect(lambda: self.close())

    def update_title(self):
        assert self.lib.library_dir
        title: str = Translations.format(
            "library_info.title", library_dir=self.lib.library_dir.stem
        )
        self.title_label.setText(f"<h2>{title}</h2>")

    def update_stats(self):
        self.entry_count_label.setText(f"<b>{self.lib.entries_count}</b>")
        self.tag_count_label.setText(f"<b>{len(self.lib.tags)}</b>")
        self.field_count_label.setText(f"<b>{len(self.lib.field_types)}</b>")
        self.namespaces_count_label.setText(f"<b>{len(self.lib.namespaces)}</b>")
        colors_total = 0
        for c in self.lib.tag_color_groups.values():
            colors_total += len(c)
        self.color_count_label.setText(f"<b>{colors_total}</b>")

        self.macros_count_label.setText("<b>1</b>")  # TODO: Implement macros system

    def showEvent(self, event: QtGui.QShowEvent):  # noqa N802
        self.update_title()
        self.update_stats()
