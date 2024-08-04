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

        r = CustomRunnable(lambda: iterator.run())
        r.done.connect(
            lambda: (
                pw.hide(),  # type: ignore
                pw.deleteLater(),  # type: ignore
                self.done.emit(),  # type: ignore
                self.reset_fixed(),
            )
        )
        QThreadPool.globalInstance().start(r)

    def increment_fixed(self):
        self.fixed += 1

    def reset_fixed(self):
        self.fixed = 0
