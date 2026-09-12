# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QPoint, Signal
from PySide6.QtWidgets import QLineEdit, QMenu, QWidget

from tagstudio.qt.views.styles.stylesheets import (
    autofill_scroll_top_focus_style,
    autofill_scroll_top_style,
)

logger = structlog.get_logger(__name__)


class AutofillLineEdit(QLineEdit):
    return_pressed = Signal()
    shift_return_pressed = Signal()
    holding_shift = Signal(bool)
    index_updated = Signal(int)

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
    def event(self, arg__1: QtCore.QEvent) -> bool:
        if arg__1.type() == QtCore.QEvent.Type.KeyPress:
            assert isinstance(arg__1, QtGui.QKeyEvent)

            if arg__1.key() == QtCore.Qt.Key.Key_Tab:
                self.index_updated.emit(1)
                return True
            elif arg__1.key() == QtCore.Qt.Key.Key_Backtab:
                self.index_updated.emit(-1)
                return True

            if arg__1.key() == QtCore.Qt.Key.Key_Shift:
                self.holding_shift.emit(True)  # noqa: FBT003

            if arg__1.key() == QtCore.Qt.Key.Key_Escape:
                self.setText("")
                self.clearFocus()
            elif (
                arg__1.key() == QtCore.Qt.Key.Key_Enter or arg__1.key() == QtCore.Qt.Key.Key_Return
            ):
                if arg__1.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier:
                    self.shift_return_pressed.emit()
                else:
                    self.return_pressed.emit()

        return super().event(arg__1)

    @override
    def keyReleaseEvent(self, arg__1: QtGui.QKeyEvent) -> None:
        if arg__1.key() == QtCore.Qt.Key.Key_Shift:
            self.holding_shift.emit(False)  # noqa: FBT003
        return super().keyReleaseEvent(arg__1)

    def show_action_menu(self, pos: QPoint) -> None:
        """Show a context menu of actions."""
        menu = QMenu(self)
        for action in self.actions():
            # Filter out icon action(s)
            if action.text():
                menu.addAction(action)
        menu.exec(self.mapToGlobal(pos))
