# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import typing

from PySide6.QtCore import QThread, Qt, QThreadPool
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from src.core.library import Library
from src.qt.helpers.function_iterator import FunctionIterator
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.modals.delete_unlinked import DeleteUnlinkedEntriesModal
from src.qt.modals.relink_unlinked import RelinkUnlinkedEntries
from src.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


ERROR = f"[ERROR]"
WARNING = f"[WARNING]"
INFO = f"[INFO]"

logging.basicConfig(format="%(message)s", level=logging.INFO)


class FixUnlinkedEntriesModal(QWidget):
    # done = Signal(int)
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver
        self.count = -1
        self.setWindowTitle(f"Fix Unlinked Entries")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(400, 300)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

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
        self.desc_widget.setText("""Each library entry is linked to a file in one of your directories. If a file linked to an entry is moved or deleted outside of TagStudio, it is then considered unlinked.
		Unlinked entries may be automatically relinked via searching your directories, manually relinked by the user, or deleted if desired.""")
        self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.missing_count = QLabel()
        self.missing_count.setObjectName("missingCountLabel")
        self.missing_count.setStyleSheet(
            # 'background:blue;'
            # 'text-align:center;'
            "font-weight:bold;"
            "font-size:14px;"
            # 'padding-top: 6px'
            ""
        )
        self.missing_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.missing_count.setText('Missing Files: N/A')

        self.refresh_button = QPushButton()
        self.refresh_button.setText("&Refresh")
        self.refresh_button.clicked.connect(lambda: self.refresh_missing_files())

        self.search_button = QPushButton()
        self.search_button.setText("&Search && Relink")
        self.relink_class = RelinkUnlinkedEntries(self.lib, self.driver)
        self.relink_class.done.connect(lambda: self.refresh_missing_files())
        self.relink_class.done.connect(lambda: self.driver.update_thumbs())
        self.search_button.clicked.connect(lambda: self.relink_class.repair_entries())

        self.manual_button = QPushButton()
        self.manual_button.setText("&Manual Relink")

        self.delete_button = QPushButton()
        self.delete_modal = DeleteUnlinkedEntriesModal(self.lib, self.driver)
        self.delete_modal.done.connect(
            lambda: self.set_missing_count(len(self.lib.missing_files))
        )
        self.delete_modal.done.connect(lambda: self.driver.update_thumbs())
        self.delete_button.setText("De&lete Unlinked Entries")
        self.delete_button.clicked.connect(lambda: self.delete_modal.show())

        # self.combo_box = QComboBox()
        # self.combo_box.setEditable(False)
        # # self.combo_box.setMaxVisibleItems(5)
        # self.combo_box.setStyleSheet('combobox-popup:0;')
        # self.combo_box.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # for df in self.lib.default_fields:
        # 	self.combo_box.addItem(f'{df["name"]} ({df["type"].replace("_", " ").title()})')

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.done_button = QPushButton()
        self.done_button.setText("&Done")
        # self.save_button.setAutoDefault(True)
        self.done_button.setDefault(True)
        self.done_button.clicked.connect(self.hide)
        # self.done_button.clicked.connect(lambda: self.done.emit(self.combo_box.currentIndex()))
        # self.save_button.clicked.connect(lambda: save_callback(widget.get_content()))
        self.button_layout.addWidget(self.done_button)

        # self.returnPressed.connect(lambda: self.done.emit(self.combo_box.currentIndex()))

        # self.done.connect(lambda x: callback(x))

        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.missing_count)
        self.root_layout.addWidget(self.refresh_button)
        self.root_layout.addWidget(self.search_button)
        self.manual_button.setHidden(True)
        self.root_layout.addWidget(self.manual_button)
        self.root_layout.addWidget(self.delete_button)
        # self.root_layout.setStretch(1,2)
        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.button_container)

        self.set_missing_count(self.count)

    def refresh_missing_files(self):
        logging.info(f"Start RMF: {QThread.currentThread()}")
        # pb = QProgressDialog(f'Scanning Library for Unlinked Entries...', None, 0,len(self.lib.entries))
        # pb.setFixedSize(432, 112)
        # pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        # pb.setWindowTitle('Scanning Library')
        # pb.setWindowModality(Qt.WindowModality.ApplicationModal)
        # pb.show()

        iterator = FunctionIterator(self.lib.refresh_missing_files)
        pw = ProgressWidget(
            window_title="Scanning Library",
            label_text=f"Scanning Library for Unlinked Entries...",
            cancel_button_text=None,
            minimum=0,
            maximum=len(self.lib.entries),
        )
        pw.show()
        iterator.value.connect(lambda v: pw.update_progress(v + 1))
        # rmf.value.connect(lambda v: pw.update_label(f'Progress: {v}'))
        r = CustomRunnable(lambda: iterator.run())
        QThreadPool.globalInstance().start(r)
        r.done.connect(
            lambda: (
                pw.hide(),
                pw.deleteLater(),
                self.set_missing_count(len(self.lib.missing_files)),
                self.delete_modal.refresh_list(),
            )
        )

        # r = CustomRunnable(lambda: self.lib.refresh_missing_files(lambda v: self.update_scan_value(pb, v)))
        # r.done.connect(lambda: (pb.hide(), pb.deleteLater(), self.set_missing_count(len(self.lib.missing_files)), self.delete_modal.refresh_list()))
        # QThreadPool.globalInstance().start(r)
        # # r.run()
        # pass

    # def update_scan_value(self, pb:QProgressDialog, value=int):
    # 	# pb.setLabelText(f'Scanning Library for Unlinked Entries ({value}/{len(self.lib.entries)})...')
    # 	pb.setValue(value)

    def set_missing_count(self, count: int):
        self.count = count
        if self.count < 0:
            self.search_button.setDisabled(True)
            self.delete_button.setDisabled(True)
            self.missing_count.setText(f"Unlinked Entries: N/A")
        elif self.count == 0:
            self.search_button.setDisabled(True)
            self.delete_button.setDisabled(True)
            self.missing_count.setText(f"Unlinked Entries: {count}")
        else:
            self.search_button.setDisabled(False)
            self.delete_button.setDisabled(False)
            self.missing_count.setText(f"Unlinked Entries: {count}")
