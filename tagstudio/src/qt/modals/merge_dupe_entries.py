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


class MergeDuplicateEntries(QObject):
    done = Signal()

    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver

    def merge_entries(self):
        iterator = FunctionIterator(self.lib.merge_dupe_entries)

        pw = ProgressWidget(
            window_title="Merging Duplicate Entries",
            label_text="",
            cancel_button_text=None,
            minimum=0,
            maximum=len(self.lib.dupe_entries),
        )
        pw.show()

        iterator.value.connect(lambda x: pw.update_progress(x))
        iterator.value.connect(
            lambda: (pw.update_label("Merging Duplicate Entries..."))
        )

        r = CustomRunnable(lambda: iterator.run())
        r.done.connect(
            lambda: (
                pw.hide(),  # type: ignore
                pw.deleteLater(),  # type: ignore
                self.done.emit(),  # type: ignore
            )
        )
        QThreadPool.globalInstance().start(r)
