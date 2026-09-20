# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from typing import override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QPushButton

if typing.TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


class ReturnButton(QPushButton):
    def __init__(self, *args, **kwargs) -> None:  # pyright: ignore
        super().__init__(*args, **kwargs)

    @override
    def keyPressEvent(self, arg__1: QtGui.QKeyEvent) -> None:
        if self.hasFocus() and arg__1.key() in {QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return}:
            self.click()

        super().keyPressEvent(arg__1)
