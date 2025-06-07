# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel

from tagstudio.qt.widgets.fields import FieldWidget


class TextWidget(FieldWidget):
    def __init__(self, title, text: str) -> None:
        super().__init__(title)
        self.setObjectName("textBox")
        self.base_layout = QHBoxLayout()
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.base_layout)
        self.text_label = QLabel()
        self.text_label.setStyleSheet("font-size: 12px")
        self.text_label.setWordWrap(True)
        self.text_label.setTextFormat(Qt.TextFormat.RichText)
        self.text_label.setOpenExternalLinks(True)
        self.text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.base_layout.addWidget(self.text_label)
        self.set_text(text)

    def set_text(self, text: str):
        text = linkify(text)
        self.text_label.setText(text)

# Regex from https://stackoverflow.com/a/6041965
def linkify(text: str):
    url_pattern = r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-*]*[\w@?^=%&\/~+#-*])"  # noqa: E501
    return re.sub(
        url_pattern,
        lambda url: f'<a href="{url.group(0)}">{url.group(0)}</a>',
        text,
        flags=re.IGNORECASE
    )
