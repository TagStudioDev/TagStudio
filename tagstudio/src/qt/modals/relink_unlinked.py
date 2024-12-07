# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import QObject, Signal
from src.core.utils.missing_files import MissingRegistry
from src.qt.widgets.progress import ProgressWidget


class RelinkUnlinkedEntries(QObject):
    done = Signal()

    def __init__(self, tracker: MissingRegistry):
        super().__init__()
        self.tracker = tracker

    def repair_entries(self):
        def displayed_text(x):
            text = f"Attempting to Relink {x}/{self.tracker.missing_files_count} Entries. \n"
            text += f"{self.tracker.files_fixed_count} Successfully Relinked."
            return text

        pw = ProgressWidget(
            window_title="Relinking Entries",
            label_text="",
            cancel_button_text=None,
            minimum=0,
            maximum=self.tracker.missing_files_count,
        )

        pw.from_iterable_function(self.tracker.fix_missing_files, displayed_text, self.done.emit)
