# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtWidgets import QHBoxLayout, QLabel

from tagstudio.qt.mixed.field_widget import FieldWidget


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
        self.base_layout.addWidget(self.text_label)
        self.set_text(text)

    def set_text(self, text: str):
        self.text_label.setText(text)
