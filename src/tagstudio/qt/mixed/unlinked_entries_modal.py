from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.qt.mixed.remove_unlinked_modal import RemoveUnlinkedEntriesModal
from tagstudio.qt.translations import Translations

if TYPE_CHECKING:
    from tagstudio.qt.controllers.library_scanner_controller import LibraryScannerController
    from tagstudio.qt.ts_qt import QtDriver


class UnlinkedEntriesModal(QWidget):
    def __init__(self, driver: "QtDriver", scanner: "LibraryScannerController"):
        super().__init__()
        self.driver = driver
        self.scanner = scanner
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

        self.refresh_unlinked_button = QPushButton(Translations["entries.generic.refresh_alt"])
        self.refresh_unlinked_button.clicked.connect(self._on_refresh)

        self.auto_relink_button = QPushButton(Translations["entries.unlinked.search_and_relink"])
        self.auto_relink_button.clicked.connect(self._on_auto_relink)

        self.remove_button = QPushButton(Translations["entries.unlinked.remove_alt"])
        self.remove_modal = RemoveUnlinkedEntriesModal(driver, scanner)
        self.remove_button.clicked.connect(self._on_remove)
        self.remove_modal.done.connect(self.update_unlinked_count)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.done_button = QPushButton(Translations["generic.done_alt"])
        self.done_button.setDefault(True)
        self.done_button.clicked.connect(self._on_done)
        self.button_layout.addWidget(self.done_button)

        self.root_layout.addWidget(self.unlinked_count_label)
        self.root_layout.addWidget(self.unlinked_desc_widget)
        self.root_layout.addWidget(self.refresh_unlinked_button)
        self.root_layout.addWidget(self.auto_relink_button)
        self.root_layout.addWidget(self.remove_button)
        self.root_layout.addStretch(1)
        self.root_layout.addStretch(2)
        self.root_layout.addWidget(self.button_container)

    def update_unlinked_count(self):
        count = self.scanner.unlinked_entries_count

        self.auto_relink_button.setDisabled(count < 1)
        self.remove_button.setDisabled(count < 1)

        count_text: str = Translations.format(
            "entries.unlinked.unlinked_count", count=count if count >= 0 else "—"
        )
        self.unlinked_count_label.setText(f"<h3>{count_text}</h3>")

    def _on_refresh(self):
        self.scanner.scan(on_finish=self.update_unlinked_count)

    def _on_auto_relink(self):
        self.scanner.tracker.fix_unlinked_entries()
        self.update_unlinked_count()

    def _on_remove(self):
        self.remove_modal.refresh_list()
        self.remove_modal.show()

    def _on_done(self):
        self.hide()
        if self.scanner.new_files_count and self.scanner.unlinked_entries_count == 0:
            self.scanner.save_new_files()
        else:
            self.driver.update_browsing_state()

    @override
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self.update_unlinked_count()
        return super().showEvent(event)

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self._on_done()
        else:
            return super().keyPressEvent(event)
