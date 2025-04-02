# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Callable
from typing import override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.qt.translations import Translations

logger = structlog.get_logger(__name__)


class PanelModal(QWidget):
    saved = Signal()

    # TODO: Separate callbacks from the buttons you want, and just generally
    # figure out what you want from this.
    def __init__(
        self,
        widget: "PanelWidget",
        title: str = "",
        window_title: str = "",
        done_callback: Callable | None = None,
        save_callback: Callable | None = None,
        has_save: bool = False,
    ):
        # [Done]
        # - OR -
        # [Cancel] [Save]
        super().__init__()
        self.widget = widget
        self.setWindowTitle(window_title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 6)

        self.title_widget = QLabel()
        self.title_widget.setObjectName("fieldTitle")
        self.title_widget.setWordWrap(True)
        self.title_widget.setStyleSheet("font-weight:bold;font-size:14px;padding-top: 6px")
        self.setTitle(title)
        self.title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        # self.cancel_button = QPushButton()
        # self.cancel_button.setText('Cancel')

        if not (save_callback or has_save):
            self.done_button = QPushButton(Translations["generic.done"])
            self.done_button.setAutoDefault(True)
            self.done_button.clicked.connect(self.hide)
            if done_callback:
                self.done_button.clicked.connect(done_callback)
            self.widget.panel_done_button = self.done_button
            self.button_layout.addWidget(self.done_button)

        if save_callback or has_save:
            self.cancel_button = QPushButton(Translations["generic.cancel"])
            self.cancel_button.clicked.connect(self.hide)
            self.cancel_button.clicked.connect(widget.reset)
            # self.cancel_button.clicked.connect(cancel_callback)
            self.widget.panel_cancel_button = self.cancel_button
            self.button_layout.addWidget(self.cancel_button)

            self.save_button = QPushButton(Translations["generic.save"])
            self.save_button.setAutoDefault(True)
            self.save_button.clicked.connect(self.hide)
            self.save_button.clicked.connect(self.saved.emit)
            self.widget.panel_save_button = self.save_button

            if done_callback:
                self.save_button.clicked.connect(done_callback)

            if save_callback:
                self.save_button.clicked.connect(lambda: save_callback(widget.get_content()))

            self.button_layout.addWidget(self.save_button)

            # trigger save button actions when pressing enter in the widget
            self.widget.add_callback(lambda: self.save_button.click())

        widget.done.connect(lambda: save_callback(widget.get_content()))

        self.root_layout.addWidget(self.title_widget)
        self.root_layout.addWidget(widget)
        widget.parent_modal = self
        self.root_layout.setStretch(1, 2)
        self.root_layout.addWidget(self.button_container)
        widget.parent_post_init()

    def closeEvent(self, event):  # noqa: N802
        if self.cancel_button:
            self.cancel_button.click()
        elif self.done_button:
            self.done_button.click()
        event.accept()

    def setTitle(self, title: str):  # noqa: N802
        self.title_widget.setText(title)


class PanelWidget(QWidget):
    """Used for widgets that go in a modal panel, ex. for editing or searching."""

    done = Signal()
    parent_modal: PanelModal = None
    panel_save_button: QPushButton | None = None
    panel_cancel_button: QPushButton | None = None
    panel_done_button: QPushButton | None = None

    def __init__(self):
        super().__init__()

    def get_content(self) -> str:
        pass

    def reset(self):
        pass

    def parent_post_init(self):
        pass

    def add_callback(self, callback: Callable, event: str = "returnPressed"):
        logger.warning(f"[PanelModal] add_callback not implemented for {self.__class__.__name__}")

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
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
            pass
        return super().keyPressEvent(event)
