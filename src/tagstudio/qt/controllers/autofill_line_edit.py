# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLineEdit,
    QWidget,
)

from tagstudio.qt.views.stylesheets.stylesheets import (
    autofill_scroll_top_focus_style,
    autofill_scroll_top_style,
)

logger = structlog.get_logger(__name__)


class AutofillLineEdit(QLineEdit):
    return_pressed = Signal()
    shift_return_pressed = Signal()
    shift_holding = Signal(bool)

    def __init__(self, popup: QWidget) -> None:
        super().__init__()
        self._popup = popup

    @override
    def focusOutEvent(self, arg__1: QtGui.QFocusEvent) -> None:
        self._popup.setStyleSheet(autofill_scroll_top_style("container"))
        return super().focusOutEvent(arg__1)

    @override
    def focusInEvent(self, arg__1: QtGui.QFocusEvent) -> None:
        self._popup.setStyleSheet(autofill_scroll_top_focus_style("container"))
        return super().focusInEvent(arg__1)

    @override
    def keyPressEvent(self, arg__1: QtGui.QKeyEvent) -> None:
        if arg__1.key() == QtCore.Qt.Key.Key_Shift:
            self.shift_holding.emit(True)  # noqa: FBT003

        if arg__1.key() == QtCore.Qt.Key.Key_Escape:
            self.setText("")
            self.clearFocus()
        elif arg__1.key() == QtCore.Qt.Key.Key_Enter or arg__1.key() == QtCore.Qt.Key.Key_Return:
            if arg__1.modifiers() and QtCore.Qt.KeyboardModifier.ShiftModifier:
                self.shift_return_pressed.emit()
            else:
                self.return_pressed.emit()

        return super().keyPressEvent(arg__1)

    @override
    def keyReleaseEvent(self, arg__1: QtGui.QKeyEvent) -> None:
        if arg__1.key() == QtCore.Qt.Key.Key_Shift:
            self.shift_holding.emit(False)  # noqa: FBT003
        return super().keyReleaseEvent(arg__1)
