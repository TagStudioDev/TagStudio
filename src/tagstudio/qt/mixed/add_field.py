# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.translations import Translations

logger = structlog.get_logger(__name__)


# NOTE: This class doesn't inherit from PanelWidget? Seems like it predates that system?
class AddFieldModal(QWidget):
    done = Signal(list)

    def __init__(self, library: Library):
        # [Done]
        # - OR -
        # [Cancel] [Save]
        super().__init__()
        self.lib = library
        self.setWindowTitle(Translations["library.field.add"])
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(400, 300)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.title_widget = QLabel(Translations["library.field.add"])
        self.title_widget.setObjectName("fieldTitle")
        self.title_widget.setWordWrap(True)
        self.title_widget.setStyleSheet("font-weight:bold;font-size:14px;padding-top: 6px;")
        self.title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.list_widget = QListWidget()

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.cancel_button = QPushButton(Translations["generic.cancel"])
        self.cancel_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton(Translations["generic.add"])
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.hide)
        self.save_button.clicked.connect(
            lambda: (
                # get userData for each selected item
                self.done.emit(self.list_widget.selectedItems())
            )
        )
        self.button_layout.addWidget(self.save_button)

        self.root_layout.addWidget(self.title_widget)
        self.root_layout.addWidget(self.list_widget)
        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.button_container)

    def show(self):
        self.list_widget.clear()
        for df in self.lib.field_types.values():
            item = QListWidgetItem(f"{df.name} ({df.type.value})")
            item.setData(Qt.ItemDataRole.UserRole, df.key)
            self.list_widget.addItem(item)
        self.list_widget.setFocus()

        super().show()

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.cancel_button.click()
        elif event.key() in (QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return):
            self.save_button.click()
        else:  # Other key presses
            pass
        return super().keyPressEvent(event)
