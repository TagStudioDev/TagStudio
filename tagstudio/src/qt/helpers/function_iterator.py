# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal


class FunctionIterator(QObject):
    """Iterate over a yielding function and emit progress as the 'value' signal."""

    value = Signal(object)

    def __init__(self, function: Callable):
        super().__init__()
        self.iterable = function

    def run(self):
        for i in self.iterable():
            self.value.emit(i)
