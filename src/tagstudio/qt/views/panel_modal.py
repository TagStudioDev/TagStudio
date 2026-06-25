# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import contextlib
from typing import Any, override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.qt.translations import Translations

logger = structlog.get_logger(__name__)


class PanelModal(QWidget):
    """A generic reusable modal panel widget."""

    done = Signal()
    saved = Signal()
    saved_data = Signal(type(Any))

    def __init__(
        self,
        widget: "PanelWidget",
        title: str = "",
        window_title: str | None = None,
        is_savable: bool = False,
        inline_title: bool = True,
    ):
        # [Done]
        # - OR -
        # [Cancel] [Save]
        super().__init__()
        self.widget = widget
        self.setWindowTitle(title if window_title is None else window_title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0 if inline_title else 12, 6, 6)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        if not is_savable:
            self.done_button = QPushButton(Translations["generic.done"])
            self.done_button.setAutoDefault(True)
            self.done_button.clicked.connect(self.hide)
            self.done_button.clicked.connect(self.done.emit)
            self.widget.panel_done_button = self.done_button
            self.button_layout.addWidget(self.done_button)
        else:
            self.cancel_button = QPushButton(Translations["generic.cancel"])
            self.cancel_button.clicked.connect(self.hide)
            self.cancel_button.clicked.connect(widget.reset)
            self.widget.panel_cancel_button = self.cancel_button
            self.button_layout.addWidget(self.cancel_button)

            self.save_button = QPushButton(Translations["generic.save"])
            self.save_button.setAutoDefault(True)
            self.save_button.clicked.connect(self.hide)
            self.save_button.clicked.connect(self.saved.emit)
            self.save_button.clicked.connect(lambda: self.saved_data.emit(widget.saved_data()))
            self.widget.panel_save_button = self.save_button
            self.button_layout.addWidget(self.save_button)

        if inline_title:
            self.title_widget = QLabel()
            self.title_widget.setObjectName("fieldTitle")
            self.title_widget.setWordWrap(True)
            self.title_widget.setStyleSheet("font-weight:bold;font-size:14px;padding-top:6px")
            self.title_widget.setText(title)
            self.title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.root_layout.addWidget(self.title_widget)

        self.root_layout.addWidget(widget)
        widget.parent_modal = self
        self.root_layout.setStretch(1, 2)
        self.root_layout.addWidget(self.button_container)
        widget.parent_post_init()

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        with contextlib.suppress(AttributeError):
            self.cancel_button.click()
        with contextlib.suppress(AttributeError):
            self.done_button.click()
        event.accept()


class PanelWidget(QWidget):
    """Used for widgets that go in a modal panel, ex. for editing or searching."""

    parent_modal: PanelModal | None = None
    panel_save_button: QPushButton | None = None
    panel_cancel_button: QPushButton | None = None
    panel_done_button: QPushButton | None = None

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
            if self.panel_cancel_button:
                self.panel_cancel_button.click()
            elif self.panel_done_button:
                self.panel_done_button.click()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.panel_save_button:
                self.panel_save_button.click()
            elif self.panel_done_button:
                self.panel_done_button.click()
        else:  # Other key presses
            super().keyPressEvent(event)
