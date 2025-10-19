# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio
import structlog
from PySide6.QtCore import Qt

from tagstudio.qt.mixed.text_field import TextWidget

logger = structlog.get_logger(__name__)


def to_anchor(url_title: str | None, url_value: str) -> str:
    if url_title is None:
        url_title = url_value

    return f'<a href="{url_value}">{url_title}</a>'


class UrlWidget(TextWidget):
    def __init__(self, title, url_title: str | None, url_value: str) -> None:
        super().__init__(title, to_anchor(url_title, url_value))
        self.setObjectName("urlLine")
        self.text_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.text_label.setOpenExternalLinks(True)
        self.text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.set_url(url_title, url_value)

    def set_url(self, url_title: str | None, url_value: str) -> None:
        self.set_text(to_anchor(url_title, url_value))
