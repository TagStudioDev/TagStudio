# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from typing import override

from PySide6.QtCore import QObject, QRunnable, Signal


class CustomRunnable(QRunnable, QObject):  # pyright: ignore[reportUnsafeMultipleInheritance]
    done = Signal()

    def __init__(self, function: Callable[..., None]) -> None:
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.setAutoDelete(False)
        self.function = function

    @override
    def run(self):
        self.function()
        self.done.emit()
        self.deleteLater()
