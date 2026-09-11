# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.merge_dupe_entries_progress import MergeDuplicateEntriesProgress
from tagstudio.qt.mixed.remove_unlinked_modal import RemoveUnlinkedEntriesModal
from tagstudio.qt.views.styles.stylesheets import header

if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


# TODO: Split to use MVC guidelines, or completely redo.
class FixUnlinkedEntriesModal(QWidget):
    def __init__(self, library: Library, driver: QtDriver):
        super().__init__()
        self.lib = library
        self.driver = driver
        self.sync_engine = driver.sync_engine

        self.unlinked_count = -1
        self.dupe_count = -1
        self.setWindowTitle(Translations["entries.unlinked.title"])
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(400, 300)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.unlinked_desc_widget = QLabel(
            Translations["entries.unlinked.description"]
            + "<br><br>"
            + Translations["entries.unlinked.description.deleted"]
            # TODO: Implement manual relinking
            # + "<br><br>"
            # + Translations["entries.unlinked.description.ambiguous"]
        )
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
        self.refresh_unlinked_button.clicked.connect(self.driver.sync_library_callback)

        self.merge_class = MergeDuplicateEntriesProgress(self.lib, self.driver)

        self.manual_button = QPushButton(Translations["entries.unlinked.relink.manual"])
        self.manual_button.setHidden(True)

        self.remove_button = QPushButton(Translations["entries.unlinked.remove_alt"])
        self.remove_modal = RemoveUnlinkedEntriesModal(self.driver, self.sync_engine)
        self.remove_modal.done.connect(
            lambda: (
                self.driver.update_browsing_state(),
                self._sync_ui_from_tracker(),
            )
        )
        self.remove_button.clicked.connect(
            lambda: (self.remove_modal.refresh_list(), self.remove_modal.show())
        )

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
        self.root_layout.addWidget(self.manual_button)
        self.root_layout.addWidget(self.remove_button)
        self.root_layout.addStretch(1)
        self.root_layout.addStretch(2)
        self.root_layout.addWidget(self.button_container)

        self.update_unlinked_count()

    def _sync_ui_from_tracker(self) -> None:
        """Refresh the UI from the tracker's current state, without rescanning the library."""
        self.set_unlinked_count()
        self.update_unlinked_count()
        self.remove_modal.refresh_list()

    def set_unlinked_count(self):
        """Sets the unlinked_entries_count in the Library to the tracker's value."""
        self.lib.unlinked_entries_count = self.sync_engine.unlinked_entries_count

    def update_unlinked_count(self):
        """Updates the UI to reflect the Library's current unlinked_entries_count."""
        count: int = self.lib.unlinked_entries_count
        syncing = self.driver.file_scan_lock  # Disabled while a sync is running

        self.remove_button.setDisabled(count < 1 or syncing)

        count_text: str = Translations.format(
            "entries.unlinked.unlinked_count", count=count if count >= 0 else "—"
        )
        self.unlinked_count_label.setText(header(count_text, 3))

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
