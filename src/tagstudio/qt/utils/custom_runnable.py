# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


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
