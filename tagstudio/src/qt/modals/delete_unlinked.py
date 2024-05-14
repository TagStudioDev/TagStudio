# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing

from PySide6.QtCore import Signal, Qt, QThreadPool
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListView,
)

from src.core.library import ItemType, Library
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.helpers.function_iterator import FunctionIterator
from src.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class DeleteUnlinkedEntriesModal(QWidget):
    done = Signal()

    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver
        self.setWindowTitle(f"Delete Unlinked Entries")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(500, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.desc_widget = QLabel()
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)
        self.desc_widget.setText(f"""
		Are you sure you want to delete the following {len(self.lib.missing_files)} entries?
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

        self.delete_button = QPushButton()
        self.delete_button.setText("&Delete")
        self.delete_button.clicked.connect(self.hide)
        self.delete_button.clicked.connect(lambda: self.delete_entries())
        self.button_layout.addWidget(self.delete_button)

        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.list_view)
        self.root_layout.addWidget(self.button_container)

    def refresh_list(self):
        self.desc_widget.setText(f"""
		Are you sure you want to delete the following {len(self.lib.missing_files)} entries?
		""")

        self.model.clear()
        for i in self.lib.missing_files:
            self.model.appendRow(QStandardItem(i))

    def delete_entries(self):
        # pb = QProgressDialog('', None, 0, len(self.lib.missing_files))
        # # pb.setMaximum(len(self.lib.missing_files))
        # pb.setFixedSize(432, 112)
        # pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        # pb.setWindowTitle('Deleting Entries')
        # pb.setWindowModality(Qt.WindowModality.ApplicationModal)
        # pb.show()

        # r = CustomRunnable(lambda: self.lib.ref(pb))
        # r.done.connect(lambda: self.done.emit())
        # # r.done.connect(lambda: self.model.clear())
        # QThreadPool.globalInstance().start(r)
        # # r.run()

        iterator = FunctionIterator(self.lib.remove_missing_files)

        pw = ProgressWidget(
            window_title="Deleting Entries",
            label_text="",
            cancel_button_text=None,
            minimum=0,
            maximum=len(self.lib.missing_files),
        )
        pw.show()

        iterator.value.connect(lambda x: pw.update_progress(x[0] + 1))
        iterator.value.connect(
            lambda x: pw.update_label(
                f"Deleting {x[0]+1}/{len(self.lib.missing_files)} Unlinked Entries"
            )
        )
        iterator.value.connect(
            lambda x: self.driver.purge_item_from_navigation(ItemType.ENTRY, x[1])
        )

        r = CustomRunnable(lambda: iterator.run())
        QThreadPool.globalInstance().start(r)
        r.done.connect(lambda: (pw.hide(), pw.deleteLater(), self.done.emit()))

    # def delete_entries_runnable(self):
    # 	deleted = []
    # 	for i, missing in enumerate(self.lib.missing_files):
    # 		# pb.setValue(i)
    # 		# pb.setLabelText(f'Deleting {i}/{len(self.lib.missing_files)} Unlinked Entries')
    # 		try:
    # 			id = self.lib.get_entry_id_from_filepath(missing)
    # 			logging.info(f'Removing Entry ID {id}:\n\t{missing}')
    # 			self.lib.remove_entry(id)
    # 			self.driver.purge_item_from_navigation(ItemType.ENTRY, id)
    # 			deleted.append(missing)
    # 		except KeyError:
    # 			logging.info(
    # 				f'{ERROR} \"{id}\" was reported as missing, but is not in the file_to_entry_id map.')
    # 		yield i
    # 	for d in deleted:
    # 		self.lib.missing_files.remove(d)
    # 	# self.driver.filter_items('')
    # 	# self.done.emit()
