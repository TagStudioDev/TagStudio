# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.missing_files import MissingRegistry
from tagstudio.qt.modals.delete_unlinked import DeleteUnlinkedEntriesModal
from tagstudio.qt.modals.merge_dupe_entries import MergeDuplicateEntries
from tagstudio.qt.modals.relink_unlinked import RelinkUnlinkedEntries
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class FixUnlinkedEntriesModal(QWidget):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver

        self.tracker = MissingRegistry(library=self.lib)

        self.missing_count = -1
        self.dupe_count = -1
        self.setWindowTitle(Translations["entries.unlinked.title"])
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(400, 300)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.unlinked_desc_widget = QLabel(Translations["entries.unlinked.description"])
        self.unlinked_desc_widget.setObjectName("unlinkedDescriptionLabel")
        self.unlinked_desc_widget.setWordWrap(True)
        self.unlinked_desc_widget.setStyleSheet("text-align:left;")

        self.missing_count_label = QLabel()
        self.missing_count_label.setObjectName("missingCountLabel")
        self.missing_count_label.setStyleSheet("font-weight:bold;font-size:14px;")
        self.missing_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dupe_count_label = QLabel()
        self.dupe_count_label.setObjectName("dupeCountLabel")
        self.dupe_count_label.setStyleSheet("font-weight:bold;font-size:14px;")
        self.dupe_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.refresh_unlinked_button = QPushButton(Translations["entries.unlinked.refresh_all"])
        self.refresh_unlinked_button.clicked.connect(self.refresh_missing_files)

        self.merge_class = MergeDuplicateEntries(self.lib, self.driver)
        self.relink_class = RelinkUnlinkedEntries(self.tracker)

        self.search_button = QPushButton(Translations["entries.unlinked.search_and_relink"])
        self.relink_class.done.connect(
            # refresh the grid
            lambda: (
                self.driver.update_browsing_state(),
                self.refresh_missing_files(),
            )
        )
        self.search_button.clicked.connect(self.relink_class.repair_entries)

        self.manual_button = QPushButton(Translations["entries.unlinked.relink.manual"])
        self.manual_button.setHidden(True)

        self.delete_button = QPushButton(Translations["entries.unlinked.delete_alt"])
        self.delete_modal = DeleteUnlinkedEntriesModal(self.driver, self.tracker)
        self.delete_modal.done.connect(
            lambda: (
                self.set_missing_count(),
                # refresh the grid
                self.driver.update_browsing_state(),
            )
        )
        self.delete_button.clicked.connect(self.delete_modal.show)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.done_button = QPushButton(Translations["generic.done_alt"])
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
        pw.setWindowTitle(Translations["library.scan_library.title"])
        pw.update_label(Translations["entries.unlinked.scanning"])

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
            self.missing_count = self.tracker.missing_file_entries_count

        if self.missing_count < 0:
            self.search_button.setDisabled(True)
            self.delete_button.setDisabled(True)
            self.missing_count_label.setText(Translations["entries.unlinked.missing_count.none"])
        else:
            # disable buttons if there are no files to fix
            self.search_button.setDisabled(self.missing_count == 0)
            self.delete_button.setDisabled(self.missing_count == 0)
            self.missing_count_label.setText(
                Translations.format("entries.unlinked.missing_count.some", count=self.missing_count)
            )

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.done_button.click()
        else:  # Other key presses
            pass
        return super().keyPressEvent(event)
