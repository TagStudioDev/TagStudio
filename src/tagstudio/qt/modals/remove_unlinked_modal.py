# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.utils.unlinked_registry import UnlinkedRegistry
from tagstudio.qt.helpers.custom_runnable import CustomRunnable
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class RemoveUnlinkedEntriesModal(QWidget):
    done = Signal()

    def __init__(self, driver: "QtDriver", tracker: UnlinkedRegistry):
        super().__init__()
        self.driver = driver
        self.tracker = tracker
        self.setWindowTitle(Translations["entries.unlinked.remove"])
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(500, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.desc_widget = QLabel(
            Translations.format(
                "entries.remove.plural.confirm",
                count=self.tracker.unlinked_entries_count,
            )
        )
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)
        self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.list_view = QListView()
        self.model = QStandardItemModel()
        self.list_view.setModel(self.model)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.cancel_button = QPushButton(Translations["generic.cancel_alt"])
        self.cancel_button.setDefault(True)
        self.cancel_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.cancel_button)

        self.delete_button = QPushButton(Translations["generic.remove_alt"])
        self.delete_button.clicked.connect(self.hide)
        self.delete_button.clicked.connect(lambda: self.remove_entries())
        self.button_layout.addWidget(self.delete_button)

        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.list_view)
        self.root_layout.addWidget(self.button_container)

    def refresh_list(self):
        self.desc_widget.setText(
            Translations.format(
                "entries.remove.plural.confirm", count=self.tracker.unlinked_entries_count
            )
        )

        self.model.clear()
        for i in self.tracker.unlinked_entries:
            item = QStandardItem(str(i.path))
            item.setEditable(False)
            self.model.appendRow(item)

    def remove_entries(self):
        pw = ProgressWidget(
            cancel_button_text=None,
            minimum=0,
            maximum=0,
        )
        pw.setWindowTitle(Translations["entries.generic.remove.removing"])
        pw.update_label(
            Translations.format(
                "entries.generic.remove.removing_count", count=self.tracker.unlinked_entries_count
            )
        )
        pw.show()

        r = CustomRunnable(self.tracker.remove_unlinked_entries)
        QThreadPool.globalInstance().start(r)
        r.done.connect(
            lambda: (
                pw.hide(),
                pw.deleteLater(),
                self.done.emit(),
            )
        )

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.cancel_button.click()
        else:  # Other key presses
            pass
        return super().keyPressEvent(event)
