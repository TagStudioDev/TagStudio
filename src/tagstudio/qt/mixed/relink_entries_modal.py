# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import QObject, Signal

from tagstudio.core.library.alchemy.registries.unlinked_registry import UnlinkedRegistry
from tagstudio.qt.mixed.progress_bar import ProgressWidget
from tagstudio.qt.translations import Translations


class RelinkUnlinkedEntries(QObject):
    done = Signal()

    def __init__(self, tracker: UnlinkedRegistry):
        super().__init__()
        self.tracker = tracker

    def repair_entries(self):
        def displayed_text(x):
            return Translations.format(
                "entries.unlinked.relink.attempting",
                index=x,
                unlinked_count=self.tracker.unlinked_entries_count,
                fixed_count=self.tracker.files_fixed_count,
            )

        pw = ProgressWidget(
            label_text="",
            cancel_button_text=None,
            minimum=0,
            maximum=self.tracker.unlinked_entries_count,
        )
        pw.setWindowTitle(Translations["entries.unlinked.relink.title"])
        pw.from_iterable_function(self.tracker.fix_unlinked_entries, displayed_text, self.done.emit)
