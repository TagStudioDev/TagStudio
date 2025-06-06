# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from collections.abc import Callable

from PySide6.QtWidgets import QLineEdit, QVBoxLayout

from tagstudio.qt.widgets.panel import PanelWidget


class EditTextLine(PanelWidget):
    def __init__(self, text):
        super().__init__()
        self.setMinimumWidth(480)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.text = text
        self.text_edit = QLineEdit()
        self.text_edit.setText(text)
        self.root_layout.addWidget(self.text_edit)

    def get_content(self) -> str:
        return self.text_edit.text()

    def reset(self):
        self.text_edit.setText(self.text)

    def add_callback(self, callback: Callable, event: str = "returnPressed"):
        if event == "returnPressed":
            self.text_edit.returnPressed.connect(callback)
        else:
            raise ValueError(f"unknown event type: {event}")
