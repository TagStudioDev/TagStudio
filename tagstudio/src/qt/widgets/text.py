# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel
from src.qt.widgets.fields import FieldWidget


class TextWidget(FieldWidget):
    def __init__(self, title, text: str) -> None:
        super().__init__(title)
        # self.item = item
        self.setObjectName("textBox")
        # self.setStyleSheet('background-color:purple;')
        self.base_layout = QHBoxLayout()
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.base_layout)
        self.text_label = QLabel()
        # self.text_label.textFormat(Qt.TextFormat.RichText)
        self.text_label.setStyleSheet("font-size: 12px")
        self.text_label.setWordWrap(True)
        self.text_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.base_layout.addWidget(self.text_label)
        self.set_text(text)

    def set_text(self, text: str):
        self.text_label.setText(text)
