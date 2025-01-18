# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library
from src.core.utils.dupe_files import DupeRegistry
from src.qt.modals.mirror_entities import MirrorEntriesModal
from src.qt.translations import Translations

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class FixDupeFilesModal(QWidget):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver
        self.count = -1
        self.filename = ""
        Translations.translate_with_setter(self.setWindowTitle, "file.duplicates.fix")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(400, 300)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)
        self.setWindowFlag(Qt.Dialog, on=True) # type: ignore

        self.tracker = DupeRegistry(library=self.lib)

        self.desc_widget = QLabel()
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)
        self.desc_widget.setStyleSheet("text-align:left;")
        Translations.translate_qobject(self.desc_widget, "file.duplicates.description")
        self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dupe_count = QLabel()
        self.dupe_count.setObjectName("dupeCountLabel")
        self.dupe_count.setStyleSheet("font-weight:bold;" "font-size:14px;" "")
        self.dupe_count.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.file_label = QLabel()
        self.file_label.setObjectName("fileLabel")
        Translations.translate_qobject(self.file_label, "file.duplicates.dupeguru.no_file")

        self.open_button = QPushButton()
        Translations.translate_qobject(self.open_button, "file.duplicates.dupeguru.load_file")
        self.open_button.clicked.connect(self.select_file)

        self.mirror_modal = MirrorEntriesModal(self.driver, self.tracker)
        self.mirror_modal.done.connect(self.refresh_dupes)

        self.mirror_button = QPushButton()
        Translations.translate_qobject(self.mirror_button, "file.duplicates.mirror_entries")
        self.mirror_button.clicked.connect(self.mirror_modal.show)
        self.mirror_desc = QLabel()
        self.mirror_desc.setWordWrap(True)
        Translations.translate_qobject(self.mirror_desc, "file.duplicates.mirror.description")

        self.advice_label = QLabel()
        self.advice_label.setWordWrap(True)
        Translations.translate_qobject(self.advice_label, "file.duplicates.dupeguru.advice")

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.done_button = QPushButton()
        Translations.translate_qobject(self.done_button, "generic.done_alt")
        self.done_button.setDefault(True)
        self.done_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.done_button)

        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.dupe_count)
        self.root_layout.addWidget(self.file_label)
        self.root_layout.addWidget(self.open_button)

        self.root_layout.addWidget(self.mirror_button)
        self.root_layout.addWidget(self.mirror_desc)
        self.root_layout.addWidget(self.advice_label)
        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.button_container)

        self.set_dupe_count(-1)

    def select_file(self):
        qfd = QFileDialog(
            self, Translations["file.duplicates.dupeguru.open_file"], str(self.lib.library_dir)
        )
        qfd.setFileMode(QFileDialog.FileMode.ExistingFile)
        qfd.setNameFilter(Translations["file.duplicates.dupeguru.file_extension"])
        if qfd.exec_():
            filename = qfd.selectedFiles()
            if filename:
                self.set_filename(filename[0])

    def set_filename(self, filename: str):
        if filename:
            self.file_label.setText(filename)
        else:
            self.file_label.setText(Translations["file.duplicates.dupeguru.no_file"])
        self.filename = filename
        self.refresh_dupes()
        self.mirror_modal.refresh_list()

    def refresh_dupes(self):
        self.tracker.refresh_dupe_files(self.filename)
        self.set_dupe_count(self.tracker.groups_count)

    def set_dupe_count(self, count: int):
        if count < 0:
            self.mirror_button.setDisabled(True)
            self.dupe_count.setText(Translations["file.duplicates.matches_uninitialized"])
        elif count == 0:
            self.mirror_button.setDisabled(True)
            self.dupe_count.setText(
                Translations.translate_formatted("file.duplicates.matches", count=count)
            )
        else:
            self.mirror_button.setDisabled(False)
            self.dupe_count.setText(
                Translations.translate_formatted("file.duplicates.matches", count=count)
            )
