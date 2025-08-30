# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.unlinked_registry import UnlinkedRegistry
from tagstudio.qt.modals.merge_dupe_entries import MergeDuplicateEntries
from tagstudio.qt.modals.relink_entries_modal import RelinkUnlinkedEntries
from tagstudio.qt.modals.remove_unlinked_modal import RemoveUnlinkedEntriesModal
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


# TODO: Break up into MVC classes, similar to fix_ignored_modal
class FixUnlinkedEntriesModal(QWidget):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver

        self.tracker = UnlinkedRegistry(lib=self.lib)

        self.unlinked_count = -1
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

        self.unlinked_count_label = QLabel()
        self.unlinked_count_label.setObjectName("unlinkedCountLabel")
        self.unlinked_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dupe_count_label = QLabel()
        self.dupe_count_label.setObjectName("dupeCountLabel")
        self.dupe_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.refresh_unlinked_button = QPushButton(Translations["entries.generic.refresh_alt"])
        self.refresh_unlinked_button.clicked.connect(self.refresh_unlinked)

        self.merge_class = MergeDuplicateEntries(self.lib, self.driver)
        self.relink_class = RelinkUnlinkedEntries(self.tracker)

        self.search_button = QPushButton(Translations["entries.unlinked.search_and_relink"])
        self.relink_class.done.connect(
            # refresh the grid
            lambda: (
                self.driver.update_browsing_state(),
                self.refresh_unlinked(),
            )
        )
        self.search_button.clicked.connect(self.relink_class.repair_entries)

        self.manual_button = QPushButton(Translations["entries.unlinked.relink.manual"])
        self.manual_button.setHidden(True)

        self.remove_button = QPushButton(Translations["entries.unlinked.remove_alt"])
        self.remove_modal = RemoveUnlinkedEntriesModal(self.driver, self.tracker)
        self.remove_modal.done.connect(
            lambda: (
                self.set_unlinked_count(),
                # refresh the grid
                self.driver.update_browsing_state(),
                self.refresh_unlinked(),
            )
        )
        self.remove_button.clicked.connect(self.remove_modal.show)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.done_button = QPushButton(Translations["generic.done_alt"])
        self.done_button.setDefault(True)
        self.done_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.done_button)

        self.root_layout.addWidget(self.unlinked_count_label)
        self.root_layout.addWidget(self.unlinked_desc_widget)
        self.root_layout.addWidget(self.refresh_unlinked_button)
        self.root_layout.addWidget(self.search_button)
        self.root_layout.addWidget(self.manual_button)
        self.root_layout.addWidget(self.remove_button)
        self.root_layout.addStretch(1)
        self.root_layout.addStretch(2)
        self.root_layout.addWidget(self.button_container)

        self.update_unlinked_count()

    def refresh_unlinked(self):
        pw = ProgressWidget(
            cancel_button_text=None,
            minimum=0,
            maximum=self.lib.entries_count,
        )
        pw.setWindowTitle(Translations["library.scan_library.title"])
        pw.update_label(Translations["entries.unlinked.scanning"])

        def update_driver_widgets():
            if (
                hasattr(self.driver, "library_info_window")
                and self.driver.library_info_window.isVisible()
            ):
                self.driver.library_info_window.update_cleanup()

        pw.from_iterable_function(
            self.tracker.refresh_unlinked_files,
            None,
            self.set_unlinked_count,
            self.update_unlinked_count,
            self.remove_modal.refresh_list,
            update_driver_widgets,
        )

    def set_unlinked_count(self):
        """Sets the unlinked_entries_count in the Library to the tracker's value."""
        self.lib.unlinked_entries_count = self.tracker.unlinked_entries_count

    def update_unlinked_count(self):
        """Updates the UI to reflect the Library's current unlinked_entries_count."""
        # Indicates that the library is new compared to the last update.
        # NOTE: Make sure set_unlinked_count() is called before this!
        if self.tracker.unlinked_entries_count > 0 and self.lib.unlinked_entries_count < 0:
            self.tracker.reset()

        count: int = self.lib.unlinked_entries_count

        self.search_button.setDisabled(count < 1)
        self.remove_button.setDisabled(count < 1)

        count_text: str = Translations.format(
            "entries.unlinked.unlinked_count", count=count if count >= 0 else "—"
        )
        self.unlinked_count_label.setText(f"<h3>{count_text}</h3>")

    @override
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self.update_unlinked_count()
        return super().showEvent(event)

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.done_button.click()
        else:  # Other key presses
            pass
        return super().keyPressEvent(event)
