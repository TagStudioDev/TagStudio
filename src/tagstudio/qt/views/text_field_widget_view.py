# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel

from tagstudio.qt.views.field_widget_view import FieldWidgetView


class TextFieldWidget(FieldWidgetView):
    """A widget representing a text field of an entry."""

    def __init__(self, title: str, text: str) -> None:
        super().__init__(title)

        # Text field
        self.setObjectName("text_field")

        self.__root_layout = QHBoxLayout()
        self.__root_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__root_layout)

        # Text label
        self.__text_label = QLabel()
        self.__text_label.setStyleSheet("font-size: 12px")
        self.__text_label.setWordWrap(True)
        self.__text_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.__text_label.setOpenExternalLinks(True)
        self.__text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.__root_layout.addWidget(self.__text_label)

        self.set_text(text)

    def set_text(self, text: str) -> None:
        """Sets the text of the field."""
        self.__text_label.setText(linkify(text))


# Regex from https://stackoverflow.com/a/6041965
def linkify(text: str) -> str:
    """Replaces any found URLs in a string with an embedded link."""
    url_pattern: str = r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#\-*]*[\w@?^=%&\/~+#\-*])"  # noqa: E501
    return re.sub(
        url_pattern,
        lambda url: f'<a href="{url.group(0)}">{url.group(0)}</a>',
        text,
        flags=re.IGNORECASE,
    )
