# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
)

from src.core.library import Library
from src.core.utils.dupe_files import DupeRegistry
from src.qt.modals.mirror_entities import MirrorEntriesModal

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class FixDupeFilesModal(QWidget):
    # done = Signal(int)
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver
        self.count = -1
        self.filename = ""
        self.setWindowTitle(QCoreApplication.translate("fix_dupes", "fix_dupes"))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(400, 300)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.tracker = DupeRegistry(library=self.lib)

        self.desc_widget = QLabel()
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)
        self.desc_widget.setStyleSheet(
            # 'background:blue;'
            "text-align:left;"
            # 'font-weight:bold;'
            # 'font-size:14px;'
            # 'padding-top: 6px'
            ""
        )
        self.desc_widget.setText(
            """TagStudio supports importing DupeGuru results to manage duplicate files."""
        )
        self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dupe_count = QLabel()
        self.dupe_count.setObjectName("dupeCountLabel")
        self.dupe_count.setStyleSheet(
            # 'background:blue;'
            # 'text-align:center;'
            "font-weight:bold;"
            "font-size:14px;"
            # 'padding-top: 6px'
            ""
        )
        self.dupe_count.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.file_label = QLabel()
        self.file_label.setObjectName("fileLabel")
        # self.file_label.setStyleSheet(
        # 								# 'background:blue;'
        # 						 		# 'text-align:center;'
        # 								'font-weight:bold;'
        # 								'font-size:14px;'
        # 								# 'padding-top: 6px'
        # 								'')
        # self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setText(QCoreApplication.translate("fix_dupes", "no_file_selected"))

        self.open_button = QPushButton()
        self.open_button.setText(QCoreApplication.translate("fix_dupes", "load_file"))
        self.open_button.clicked.connect(self.select_file)

        self.mirror_modal = MirrorEntriesModal(self.driver, self.tracker)
        self.mirror_modal.done.connect(self.refresh_dupes)

        self.mirror_button = QPushButton()
        self.mirror_button.setText(QCoreApplication.translate("fix_dupes", "mirror_entries"))
        self.mirror_button.clicked.connect(self.mirror_modal.show)
        self.mirror_desc = QLabel()
        self.mirror_desc.setWordWrap(True)
        self.mirror_desc.setText(
                QCoreApplication.translate("fix_dupes", "mirror_description")
        )

        # self.mirror_delete_button = QPushButton()
        # self.mirror_delete_button.setText('Mirror && Delete')

        self.advice_label = QLabel()
        self.advice_label.setWordWrap(True)
        self.advice_label.setText(
            QCoreApplication.translate("fix_dupes", "advice_label")
        )

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.done_button = QPushButton()
        self.done_button.setText(QCoreApplication.translate("generic", "done"))
        # self.save_button.setAutoDefault(True)
        self.done_button.setDefault(True)
        self.done_button.clicked.connect(self.hide)
        # self.done_button.clicked.connect(lambda: self.done.emit(self.combo_box.currentIndex()))
        # self.save_button.clicked.connect(lambda: save_callback(widget.get_content()))
        self.button_layout.addWidget(self.done_button)

        # self.returnPressed.connect(lambda: self.done.emit(self.combo_box.currentIndex()))

        # self.done.connect(lambda x: callback(x))

        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.dupe_count)
        self.root_layout.addWidget(self.file_label)
        self.root_layout.addWidget(self.open_button)
        # self.mirror_delete_button.setHidden(True)

        self.root_layout.addWidget(self.mirror_button)
        self.root_layout.addWidget(self.mirror_desc)
        # self.root_layout.addWidget(self.mirror_delete_button)
        self.root_layout.addWidget(self.advice_label)
        # self.root_layout.setStretch(1,2)
        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.button_container)

        self.set_dupe_count(-1)

    def select_file(self):
        qfd = QFileDialog(self, QCoreApplication.translate("fix_dupes", "open_results_file"), str(self.lib.library_dir))
        qfd.setFileMode(QFileDialog.FileMode.ExistingFile)
        qfd.setNameFilter(QCoreApplication.translate("fix_dupes", "name_filter"))
        if qfd.exec_():
            filename = qfd.selectedFiles()
            if filename:
                self.set_filename(filename[0])

    def set_filename(self, filename: str):
        if filename:
            self.file_label.setText(filename)
        else:
            self.file_label.setText(QCoreApplication.translate("fix_dupes", "no_file_selected"))
        self.filename = filename
        self.refresh_dupes()
        self.mirror_modal.refresh_list()

    def refresh_dupes(self):
        self.tracker.refresh_dupe_files(self.filename)
        self.set_dupe_count(self.tracker.groups_count)

    def set_dupe_count(self, count: int):
        if count < 0:
            self.mirror_button.setDisabled(True)
            self.dupe_count.setText(QCoreApplication.translate("fix_dupes", "no_file_match"))
        elif count == 0:
            self.mirror_button.setDisabled(True)
            self.dupe_count.setText(QCoreApplication.translate("fix_dupes", "number_file_match"))
        else:
            self.mirror_button.setDisabled(False)
            self.dupe_count.setText(QCoreApplication.translate("fix_dupes", "number_file_match"))
