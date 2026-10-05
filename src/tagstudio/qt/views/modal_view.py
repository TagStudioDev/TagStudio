# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox, QLabel, QVBoxLayout

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.views.styles.stylesheets import PAD, header

logger = structlog.get_logger(__name__)


class ModalView(QVBoxLayout):
    """A generic reusable modal panel widget."""

    def __init__(
        self,
        content_widget: ModalContent,
        title: str = "",
        is_savable: bool = False,
        inline_title: bool = True,
        inline_title_level: int = 3,
    ):
        super().__init__()
        self.content_widget = content_widget
        self.setContentsMargins(PAD, PAD if inline_title else PAD * 2, PAD, PAD)

        self.button_box = QDialogButtonBox()
        self.button_box.setContentsMargins(PAD, PAD, PAD, PAD)

        if not is_savable:
            done_button = self.button_box.addButton(
                Translations["generic.done"], QDialogButtonBox.ButtonRole.AcceptRole
            )
            done_button.setAutoDefault(True)
            self.content_widget.done_button = done_button
        else:
            cancel_button = self.button_box.addButton(
                Translations["generic.cancel"], QDialogButtonBox.ButtonRole.RejectRole
            )
            self.content_widget.cancel_button = cancel_button

            save_button = self.button_box.addButton(
                Translations["generic.save"], QDialogButtonBox.ButtonRole.AcceptRole
            )
            save_button.setAutoDefault(True)
            self.content_widget.save_button = save_button

        if inline_title:
            self.title_label = QLabel()
            self.title_label.setObjectName("fieldTitle")
            self.title_label.setWordWrap(True)
            self.title_label.setText(header(title, inline_title_level))
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.addWidget(self.title_label)

        self.addWidget(content_widget)
        self.setStretch(1, 2)
        self.addWidget(self.button_box)
