# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing

from PySide6.QtCore import QObject, Signal, QThreadPool

from src.core.library import Library
from src.qt.helpers.function_iterator import FunctionIterator
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class RelinkUnlinkedEntries(QObject):
    done = Signal()

    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver
        self.fixed = 0

    def repair_entries(self):
        # pb = QProgressDialog('', None, 0, len(self.lib.missing_files))
        # # pb.setMaximum(len(self.lib.missing_files))
        # pb.setFixedSize(432, 112)
        # pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        # pb.setWindowTitle('Relinking Entries')
        # pb.setWindowModality(Qt.WindowModality.ApplicationModal)
        # pb.show()

        # r = CustomRunnable(lambda: self.repair_entries_runnable(pb))
        # r.done.connect(lambda: self.done.emit())
        # # r.done.connect(lambda: self.model.clear())
        # QThreadPool.globalInstance().start(r)
        # # r.run()

        iterator = FunctionIterator(self.lib.fix_missing_files)

        pw = ProgressWidget(
            window_title="Relinking Entries",
            label_text="",
            cancel_button_text=None,
            minimum=0,
            maximum=len(self.lib.missing_files),
        )
        pw.show()

        iterator.value.connect(lambda x: pw.update_progress(x[0] + 1))
        iterator.value.connect(
            lambda x: (
                self.increment_fixed() if x[1] else (),
                pw.update_label(
                    f"Attempting to Relink {x[0]+1}/{len(self.lib.missing_files)} Entries, {self.fixed} Successfully Relinked"
                ),
            )
        )
        # iterator.value.connect(lambda x: self.driver.purge_item_from_navigation(ItemType.ENTRY, x[1]))

        r = CustomRunnable(lambda: iterator.run())
        r.done.connect(
            lambda: (pw.hide(), pw.deleteLater(), self.done.emit(), self.reset_fixed())
        )
        QThreadPool.globalInstance().start(r)

    def increment_fixed(self):
        self.fixed += 1

    def reset_fixed(self):
        self.fixed = 0

    # def repair_entries_runnable(self, pb: QProgressDialog):
    # 	fixed = 0
    # 	for i in self.lib.fix_missing_files():
    # 		if i[1]:
    # 			fixed += 1
    # 		pb.setValue(i[0])
    # 		pb.setLabelText(f'Attempting to Relink {i[0]+1}/{len(self.lib.missing_files)} Entries, {fixed} Successfully Relinked')

    # for i, missing in enumerate(self.lib.missing_files):
    # 	pb.setValue(i)
    # 	pb.setLabelText(f'Relinking {i}/{len(self.lib.missing_files)} Unlinked Entries')
    # 	self.lib.fix_missing_files()
    # 	try:
    # 		id = self.lib.get_entry_id_from_filepath(missing)
    # 		logging.info(f'Removing Entry ID {id}:\n\t{missing}')
    # 		self.lib.remove_entry(id)
    # 		self.driver.purge_item_from_navigation(ItemType.ENTRY, id)
    # 		deleted.append(missing)
    # 	except KeyError:
    # 		logging.info(
    # 			f'{ERROR} \"{id}\" was reported as missing, but is not in the file_to_entry_id map.')
    # for d in deleted:
    # 	self.lib.missing_files.remove(d)
