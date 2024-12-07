# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing
from time import sleep

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.utils.dupe_files import DupeRegistry
from src.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class MirrorEntriesModal(QWidget):
    done = Signal()

    def __init__(self, driver: "QtDriver", tracker: DupeRegistry):
        super().__init__()
        self.driver = driver
        self.setWindowTitle("Mirror Entries")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(500, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)
        self.tracker = tracker

        self.desc_widget = QLabel()
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)

        self.desc_widget.setText(f"""
		Are you sure you want to mirror the following {self.tracker.groups_count} Entries?
		""")
        self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.list_view = QListView()
        self.model = QStandardItemModel()
        self.list_view.setModel(self.model)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.cancel_button = QPushButton()
        self.cancel_button.setText("&Cancel")
        self.cancel_button.setDefault(True)
        self.cancel_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.cancel_button)

        self.mirror_button = QPushButton()
        self.mirror_button.setText("&Mirror")
        self.mirror_button.clicked.connect(self.hide)
        self.mirror_button.clicked.connect(self.mirror_entries)
        self.button_layout.addWidget(self.mirror_button)

        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.list_view)
        self.root_layout.addWidget(self.button_container)

    def refresh_list(self):
        self.desc_widget.setText(f"""
		Are you sure you want to mirror the following {self.tracker.groups_count} Entries?
		""")

        self.model.clear()
        for i in self.tracker.groups:
            self.model.appendRow(QStandardItem(str(i)))

    def mirror_entries(self):
        def displayed_text(x):
            return f"Mirroring {x + 1}/{self.tracker.groups_count} Entries..."

        pw = ProgressWidget(
            window_title="Mirroring Entries",
            label_text="",
            cancel_button_text=None,
            minimum=0,
            maximum=self.tracker.groups_count,
        )

        pw.from_iterable_function(
            self.mirror_entries_runnable,
            displayed_text,
            self.driver.preview_panel.update_widgets,
            self.done.emit,
        )

    def mirror_entries_runnable(self):
        mirrored: list = []
        lib = self.driver.lib
        for i, entries in enumerate(self.tracker.groups):
            lib.mirror_entry_fields(*entries)
            sleep(0.005)
            yield i

        for d in mirrored:
            self.tracker.groups.remove(d)
