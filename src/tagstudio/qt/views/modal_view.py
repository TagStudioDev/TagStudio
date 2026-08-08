# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.stylesheets.stylesheets import header

logger = structlog.get_logger(__name__)


class ModalView(QVBoxLayout):
    """A generic reusable modal panel widget."""

    def __init__(
        self,
        content_widget: ModalContent,
        title: str = "",
        is_savable: bool = False,
        inline_title: bool = True,
    ):
        super().__init__()
        self.content_widget = content_widget
        self.setContentsMargins(6, 6 if inline_title else 12, 6, 6)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        # [Done]
        # - OR -
        # [Cancel] [Save]
        if not is_savable:
            done_button = QPushButton(Translations["generic.done"])
            done_button.setAutoDefault(True)
            self.content_widget.done_button = done_button
            self.button_layout.addWidget(done_button)
        else:
            cancel_button = QPushButton(Translations["generic.cancel"])
            self.content_widget.cancel_button = cancel_button
            self.button_layout.addWidget(cancel_button)

            save_button = QPushButton(Translations["generic.save"])
            save_button.setAutoDefault(True)
            self.content_widget.save_button = save_button
            self.button_layout.addWidget(save_button)

        if inline_title:
            self.title_label = QLabel()
            self.title_label.setObjectName("fieldTitle")
            self.title_label.setWordWrap(True)
            self.title_label.setText(header(title, 3))
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.addWidget(self.title_label)

        self.addWidget(content_widget)
        self.setStretch(1, 2)
        self.addWidget(self.button_container)
        content_widget.parent_post_init()
