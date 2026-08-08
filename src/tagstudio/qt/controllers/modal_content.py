# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import Any, override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QWidget

logger = structlog.get_logger(__name__)


class ModalContent(QWidget):
    """Base class for widgets that go inside a Modal widget."""

    save_button: QPushButton | None = None
    cancel_button: QPushButton | None = None
    done_button: QPushButton | None = None

    def __init__(self):
        super().__init__()

    def saved_data(self) -> Any:  # pyright: ignore[reportExplicitAny]
        return None

    def reset(self) -> None:
        pass

    def parent_post_init(self) -> None:
        pass

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.cancel_button:
                self.cancel_button.click()
            elif self.done_button:
                self.done_button.click()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.save_button:
                self.save_button.click()
            elif self.done_button:
                self.done_button.click()
        else:  # Other key presses
            super().keyPressEvent(event)
