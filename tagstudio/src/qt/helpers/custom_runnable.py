# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import QObject, QRunnable, Signal


class CustomRunnable(QRunnable, QObject):
    done = Signal()

    def __init__(self, function) -> None:
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.function = function

    def run(self):
        self.function()
        self.done.emit()
