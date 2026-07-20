# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import contextlib
from typing import Any, override

import structlog
from PySide6 import QtGui
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget

from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.views.modal_view import ModalView

logger = structlog.get_logger(__name__)


class Modal(QWidget):
    """A generic modal window widget with common signals and styling."""

    done = Signal()
    saved = Signal()
    saved_data = Signal(type(Any))

    def __init__(
        self,
        content_widget: ModalContent,
        title: str = "",
        window_title: str | None = None,
        is_savable: bool = False,
        inline_title: bool = True,
    ):
        super().__init__()
        self.setWindowTitle(title if window_title is None else window_title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setLayout(
            ModalView(
                content_widget=content_widget,
                title=title,
                is_savable=is_savable,
                inline_title=inline_title,
            )
        )

        # [Done]
        # - OR -
        # [Cancel] [Save]
        if not is_savable:
            done_button = self.layout().content_widget.done_button
            if done_button:
                done_button.clicked.connect(self.hide)
                done_button.clicked.connect(self.done.emit)
        else:
            cancel_button = self.layout().content_widget.cancel_button
            if cancel_button:
                cancel_button.clicked.connect(self.hide)
                cancel_button.clicked.connect(content_widget.reset)

            save_button = self.layout().content_widget.save_button
            if save_button:
                save_button.clicked.connect(self.hide)
                save_button.clicked.connect(self.saved.emit)
                save_button.clicked.connect(
                    lambda: self.saved_data.emit(content_widget.saved_data())
                )

        content_widget.parent_post_init()

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        with contextlib.suppress(AttributeError):
            cancel_button = self.layout().content_widget.cancel_button
            if cancel_button:
                cancel_button.click()
        with contextlib.suppress(AttributeError):
            done_button = self.layout().content_widget.done_button
            if done_button:
                done_button.click()
        event.accept()

    @override
    def layout(self) -> ModalView:
        """Return the typed layout for this widget."""
        return super().layout()  # pyright: ignore[reportReturnType]
