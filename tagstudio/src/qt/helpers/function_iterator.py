# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from types import FunctionType

from PySide6.QtCore import Signal, QObject


class FunctionIterator(QObject):
    """Iterates over a yielding function and emits progress as the 'value' signal.\n\nThread-Safe Guarantee™"""

    value = Signal(object)

    def __init__(self, function: FunctionType):
        super().__init__()
        self.iterable = function

    def run(self):
        for i in self.iterable():
            self.value.emit(i)
