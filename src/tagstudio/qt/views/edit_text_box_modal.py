# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout

from tagstudio.qt.views.panel_modal import PanelWidget


class EditTextBox(PanelWidget):
    def __init__(self, text):
        super().__init__()
        self.setMinimumSize(480, 480)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.text = text
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlainText(text)
        self.root_layout.addWidget(self.text_edit)

    def get_content(self) -> str:
        return self.text_edit.toPlainText()

    def reset(self):
        self.text_edit.setPlainText(self.text)
