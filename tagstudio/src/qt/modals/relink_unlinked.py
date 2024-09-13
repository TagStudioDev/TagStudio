# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import QObject, QThreadPool, Signal
from src.core.utils.missing_files import MissingRegistry
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.helpers.function_iterator import FunctionIterator
from src.qt.widgets.progress import ProgressWidget


class RelinkUnlinkedEntries(QObject):
    done = Signal()

    def __init__(self, tracker: MissingRegistry):
        super().__init__()
        self.tracker = tracker

    def repair_entries(self):
        iterator = FunctionIterator(self.tracker.fix_missing_files)

        pw = ProgressWidget(
            window_title="Relinking Entries",
            label_text="",
            cancel_button_text=None,
            minimum=0,
            maximum=self.tracker.missing_files_count,
        )

        pw.show()

        iterator.value.connect(
            lambda idx: (
                pw.update_progress(idx),
                pw.update_label(
                    f"Attempting to Relink {idx}/{self.tracker.missing_files_count} Entries. "
                    f"{self.tracker.files_fixed_count} Successfully Relinked."
                ),
            )
        )

        r = CustomRunnable(iterator.run)
        r.done.connect(
            lambda: (
                pw.hide(),
                pw.deleteLater(),
                self.done.emit(),
            )
        )
        QThreadPool.globalInstance().start(r)
