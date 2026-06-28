# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

import structlog

from tagstudio.qt.views.edit_text_view import EditTextView

logger = structlog.get_logger(__name__)


class EditText(EditTextView):
    def __init__(self, name: str, text: str | None, is_multiline: bool = False):
        super().__init__()
        self.name_field.setText(name)

        self.text = text
        self.is_multiline: bool = is_multiline

        self.multiline_checkbox.setChecked(is_multiline)
        self.multiline_checkbox.clicked.connect(lambda checked: self.on_multiline_checked(checked))

        if self.is_multiline:
            self.text_line.hide()
            self.text_line_stretch.hide()
            self.text_box.setPlainText(self.text or "")
        else:
            self.text_box.hide()
            self.text_line.setText(self.text or "")

    def on_multiline_checked(self, checked: bool):
        was_multiline = self.is_multiline
        self.is_multiline = checked

        if was_multiline:
            self.text = self.text_box.toPlainText()
            self.text_box.hide()
            self.text_line.setText(self.text)
            self.text_line.show()
            self.text_line_stretch.show()
        else:
            self.text = self.text_line.text()
            self.text_line.hide()
            self.text_line_stretch.hide()
            self.text_box.setPlainText(self.text)
            self.text_box.show()

    @override
    def parent_post_init(self):
        if self.is_multiline:
            self.text_box.setFocus()
        else:
            self.text_line.setFocus()

    @override
    def saved_data(self) -> dict[str, str | bool]:
        return {
            "name": self.name_field.text(),
            "value": self.text_box.toPlainText() if self.is_multiline else self.text_line.text(),
            "is_multiline": self.is_multiline,
        }

    @override
    def reset(self):
        self.text_box.setPlainText(self.text or "")
