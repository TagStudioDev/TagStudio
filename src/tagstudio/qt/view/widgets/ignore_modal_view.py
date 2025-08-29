# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from tagstudio.core.constants import IGNORE_NAME
from tagstudio.core.library.alchemy.library import Library, Tag
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.panel import PanelWidget

logger = structlog.get_logger(__name__)


class IgnoreModalView(PanelWidget):
    on_edit = Signal(Tag)

    def __init__(self, library: Library) -> None:
        super().__init__()
        self.lib = library

        self.setMinimumSize(640, 460)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.text_edit = QPlainTextEdit()
        font = QFont()
        font.setFamily("monospace")
        font.setFixedPitch(True)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)

        self.open_button = QPushButton(
            Translations.format("ignore.open_file", ts_ignore=IGNORE_NAME)
        )

        # Add Widgets to Layout ================================================
        self.root_layout.addWidget(self.text_edit)
        self.root_layout.addWidget(self.open_button)
