# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio
from collections.abc import Callable

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelWidget


class EditUrl(PanelWidget):
    def __init__(self, url_title: str | None, url_value: str | None):
        super().__init__()
        self.url_title = url_title
        self.url_value = url_value

        self.setMinimumWidth(480)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        # Edit title
        self.edit_title_widget = QWidget()
        self.edit_title_layout = QHBoxLayout(self.edit_title_widget)

        self.edit_title_label = QLabel(Translations["field.url.edit_title"])
        self.edit_title_input = QLineEdit()
        self.edit_title_input.setText(self.url_title or "")

        self.edit_title_layout.addWidget(self.edit_title_label)
        self.edit_title_layout.addWidget(self.edit_title_input)

        # Edit URL
        self.edit_url_widget = QWidget()
        self.edit_url_layout = QHBoxLayout(self.edit_url_widget)

        self.edit_url_label = QLabel(Translations["field.url.edit_url"])
        self.edit_url_input = QLineEdit()
        self.edit_url_input.setText(self.url_value or "")

        self.edit_url_layout.addWidget(self.edit_url_label)
        self.edit_url_layout.addWidget(self.edit_url_input)

        self.root_layout.addWidget(self.edit_title_widget)
        self.root_layout.addWidget(self.edit_url_widget)

    def get_content(self):
        # Ensure that blank values preserve being None
        url_title: str | None = self.edit_title_input.text()
        if url_title == "":
            url_title = None

        url_value: str | None = self.edit_url_input.text()
        if url_value == "":
            url_value = None

        return url_title, url_value

    def reset(self):
        self.edit_title_input.setText(self.url_title or "")
        self.edit_url_input.setText(self.url_value or "")

    def add_callback(self, callback: Callable, event: str = "returnPressed"):
        if event == "returnPressed":
            self.edit_title_input.returnPressed.connect(callback)
            self.edit_url_input.returnPressed.connect(callback)
        else:
            raise ValueError(f"unknown event type: {event}")
