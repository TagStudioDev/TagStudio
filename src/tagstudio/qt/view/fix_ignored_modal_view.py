# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.translations import Translations

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class FixIgnoredEntriesModalView(QWidget):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver

        self.setWindowTitle(Translations["entries.ignored.title"])
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(400, 300)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.ignored_desc_widget = QLabel(Translations["entries.ignored.description"])
        self.ignored_desc_widget.setObjectName("ignoredDescriptionLabel")
        self.ignored_desc_widget.setWordWrap(True)
        self.ignored_desc_widget.setStyleSheet("text-align:left;")

        self.ignored_count_label = QLabel()
        self.ignored_count_label.setObjectName("ignoredCountLabel")
        self.ignored_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.refresh_ignored_button = QPushButton(Translations["entries.generic.refresh_alt"])
        self.remove_button = QPushButton(Translations["entries.ignored.remove_alt"])

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.done_button = QPushButton(Translations["generic.done_alt"])
        self.done_button.setDefault(True)
        self.button_layout.addWidget(self.done_button)

        self.root_layout.addWidget(self.ignored_count_label)
        self.root_layout.addWidget(self.ignored_desc_widget)
        self.root_layout.addWidget(self.refresh_ignored_button)
        self.root_layout.addWidget(self.remove_button)
        self.root_layout.addStretch(1)
        self.root_layout.addStretch(2)
        self.root_layout.addWidget(self.button_container)

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.done_button.click()
        else:  # Other key presses
            pass
        return super().keyPressEvent(event)
