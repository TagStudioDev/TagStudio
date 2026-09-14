# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel


class TextDataView(QHBoxLayout):
    """The layout used for a TextData widget."""

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        self.text_label = QLabel()
        self.text_label.setStyleSheet("font-size: 12px")
        self.text_label.setWordWrap(True)
        self.text_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.text_label.setOpenExternalLinks(True)
        self.text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.addWidget(self.text_label)
