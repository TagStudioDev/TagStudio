# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtWidgets import QVBoxLayout, QLineEdit

from src.qt.widgets import PanelWidget


class EditTextLine(PanelWidget):
    def __init__(self, text):
        super().__init__()
        # self.setLayout()
        self.setMinimumWidth(480)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.text = text
        self.text_edit = QLineEdit()
        self.text_edit.setText(text)
        self.text_edit.returnPressed.connect(self.done.emit)
        self.root_layout.addWidget(self.text_edit)

    def get_content(self) -> str:
        return self.text_edit.text()

    def reset(self):
        self.text_edit.setText(self.text)
