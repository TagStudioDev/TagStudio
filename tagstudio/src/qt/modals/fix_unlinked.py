# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from src.core.library import Library
from src.core.utils.missing_files import MissingRegistry
from src.qt.modals.delete_unlinked import DeleteUnlinkedEntriesModal
from src.qt.modals.merge_dupe_entries import MergeDuplicateEntries
from src.qt.modals.relink_unlinked import RelinkUnlinkedEntries
from src.qt.translations import Translations
from src.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class FixUnlinkedEntriesModal(QWidget):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver

        self.tracker = MissingRegistry(library=self.lib)

        self.missing_count = -1
        self.dupe_count = -1
        Translations.translate_with_setter(self.setWindowTitle, "entries.unlinked.title")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(400, 300)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)
        self.setWindowFlag(Qt.Dialog, on=True) # type: ignore

        self.unlinked_desc_widget = QLabel()
        self.unlinked_desc_widget.setObjectName("unlinkedDescriptionLabel")
        self.unlinked_desc_widget.setWordWrap(True)
        self.unlinked_desc_widget.setStyleSheet("text-align:left;")
        Translations.translate_qobject(self.unlinked_desc_widget, "entries.unlinked.description")

        self.missing_count_label = QLabel()
        self.missing_count_label.setObjectName("missingCountLabel")
        self.missing_count_label.setStyleSheet("font-weight:bold;" "font-size:14px;")
        self.missing_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dupe_count_label = QLabel()
        self.dupe_count_label.setObjectName("dupeCountLabel")
        self.dupe_count_label.setStyleSheet("font-weight:bold;" "font-size:14px;")
        self.dupe_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.refresh_unlinked_button = QPushButton()
        Translations.translate_qobject(self.refresh_unlinked_button, "entries.unlinked.refresh_all")
        self.refresh_unlinked_button.clicked.connect(self.refresh_missing_files)

        self.merge_class = MergeDuplicateEntries(self.lib, self.driver)
        self.relink_class = RelinkUnlinkedEntries(self.tracker)

        self.search_button = QPushButton()
        Translations.translate_qobject(self.search_button, "entries.unlinked.search_and_relink")
        self.relink_class.done.connect(
            # refresh the grid
            lambda: (
                self.driver.filter_items(),
                self.refresh_missing_files(),
            )
        )
        self.search_button.clicked.connect(self.relink_class.repair_entries)

        self.manual_button = QPushButton()
        Translations.translate_qobject(self.manual_button, "entries.unlinked.relink.manual")
        self.manual_button.setHidden(True)

        self.delete_button = QPushButton()
        self.delete_modal = DeleteUnlinkedEntriesModal(self.driver, self.tracker)
        self.delete_modal.done.connect(
            lambda: (
                self.set_missing_count(),
                # refresh the grid
                self.driver.filter_items(),
            )
        )
        Translations.translate_qobject(self.delete_button, "entries.unlinked.delete_alt")
        self.delete_button.clicked.connect(self.delete_modal.show)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.done_button = QPushButton()
        Translations.translate_qobject(self.done_button, "generic.done_alt")
        self.done_button.setDefault(True)
        self.done_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.done_button)

        self.root_layout.addWidget(self.missing_count_label)
        self.root_layout.addWidget(self.unlinked_desc_widget)
        self.root_layout.addWidget(self.refresh_unlinked_button)
        self.root_layout.addWidget(self.search_button)
        self.root_layout.addWidget(self.manual_button)
        self.root_layout.addWidget(self.delete_button)
        self.root_layout.addStretch(1)
        self.root_layout.addStretch(2)
        self.root_layout.addWidget(self.button_container)

        self.set_missing_count(self.missing_count)

    def refresh_missing_files(self):
        pw = ProgressWidget(
            cancel_button_text=None,
            minimum=0,
            maximum=self.lib.entries_count,
        )
        Translations.translate_with_setter(pw.setWindowTitle, "library.scan_library.title")
        Translations.translate_with_setter(pw.update_label, "entries.unlinked.scanning")

        pw.from_iterable_function(
            self.tracker.refresh_missing_files,
            None,
            self.set_missing_count,
            self.delete_modal.refresh_list,
        )

    def set_missing_count(self, count: int | None = None):
        if count is not None:
            self.missing_count = count
        else:
            self.missing_count = self.tracker.missing_files_count

        if self.missing_count < 0:
            self.search_button.setDisabled(True)
            self.delete_button.setDisabled(True)
            self.missing_count_label.setText(Translations["entries.unlinked.missing_count.none"])
        else:
            # disable buttons if there are no files to fix
            self.search_button.setDisabled(self.missing_count == 0)
            self.delete_button.setDisabled(self.missing_count == 0)
            self.missing_count_label.setText(
                Translations.translate_formatted(
                    "entries.unlinked.missing_count.some", count=self.missing_count
                )
            )
