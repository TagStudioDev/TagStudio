# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing

from PySide6.QtCore import QObject, Signal
from src.core.library import Library
from src.core.utils.dupe_files import DupeRegistry
from src.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class MergeDuplicateEntries(QObject):
    done = Signal()

    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver
        self.tracker = DupeRegistry(library=self.lib)

    def merge_entries(self):
        pw = ProgressWidget(
            window_title="Merging Duplicate Entries",
            label_text="Merging Duplicate Entries...",
            cancel_button_text=None,
            minimum=0,
            maximum=self.tracker.groups_count,
        )

        pw.from_iterable_function(self.tracker.merge_dupe_entries, None, self.done.emit)
