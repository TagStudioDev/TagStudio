# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import QObject, Signal
from src.core.utils.missing_files import MissingRegistry
from src.qt.translations import Translations
from src.qt.widgets.progress import ProgressWidget


class RelinkUnlinkedEntries(QObject):
    done = Signal()

    def __init__(self, tracker: MissingRegistry):
        super().__init__()
        self.tracker = tracker

    def repair_entries(self):
        def displayed_text(x):
            return Translations["entries.unlinked.relink.attempting"].format(
                idx=x,
                missing_count=self.tracker.missing_file_entries_count,
                fixed_count=self.tracker.files_fixed_count,
            )

        pw = ProgressWidget(
            label_text="",
            cancel_button_text=None,
            minimum=0,
            maximum=self.tracker.missing_file_entries_count,
        )
        pw.setWindowTitle(Translations["entries.unlinked.relink.title"])

        pw.from_iterable_function(self.tracker.fix_unlinked_entries, displayed_text, self.done.emit)
