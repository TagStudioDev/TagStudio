# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing

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
from src.core.utils.missing_files import MissingRegistry
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.translations import Translations
from src.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class DeleteUnlinkedEntriesModal(QWidget):
    done = Signal()

    def __init__(self, driver: "QtDriver", tracker: MissingRegistry):
        super().__init__()
        self.driver = driver
        self.tracker = tracker
        Translations.translate_with_setter(self.setWindowTitle, "entries.unlinked.delete")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(500, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.desc_widget = QLabel()
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)
        Translations.translate_qobject(
            self.desc_widget,
            "entries.unlinked.delete.confirm",
            count=self.tracker.missing_files_count,
        )
        self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.list_view = QListView()
        self.model = QStandardItemModel()
        self.list_view.setModel(self.model)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.cancel_button = QPushButton()
        Translations.translate_qobject(self.cancel_button, "generic.cancel_alt")
        self.cancel_button.setDefault(True)
        self.cancel_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.cancel_button)

        self.delete_button = QPushButton()
        Translations.translate_qobject(self.delete_button, "generic.delete_alt")
        self.delete_button.clicked.connect(self.hide)
        self.delete_button.clicked.connect(lambda: self.delete_entries())
        self.button_layout.addWidget(self.delete_button)

        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.list_view)
        self.root_layout.addWidget(self.button_container)

    def refresh_list(self):
        self.desc_widget.setText(
            Translations.translate_formatted(
                "entries.unlinked.delete.confirm", count=self.tracker.missing_files_count
            )
        )

        self.model.clear()
        for i in self.tracker.missing_file_entries:
            item = QStandardItem(str(i.path))
            item.setEditable(False)
            self.model.appendRow(item)

    def delete_entries(self):
        def displayed_text(x):
            return Translations.translate_formatted(
                "entries.unlinked.delete.deleting_count",
                idx=x,
                count=self.tracker.missing_files_count,
            )

        pw = ProgressWidget(
            cancel_button_text=None,
            minimum=0,
            maximum=0,
        )
        Translations.translate_with_setter(pw.setWindowTitle, "entries.unlinked.delete.deleting")
        Translations.translate_with_setter(pw.update_label, "entries.unlinked.delete.deleting")
        pw.show()

        r = CustomRunnable(self.tracker.execute_deletion)
        QThreadPool.globalInstance().start(r)
        r.done.connect(
            lambda: (
                pw.hide(),
                pw.deleteLater(),
                self.done.emit(),
            )
        )
