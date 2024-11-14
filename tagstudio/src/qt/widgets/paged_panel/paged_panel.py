# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from src.qt.widgets.paged_panel.paged_panel_state import PagedPanelState

logger = structlog.get_logger(__name__)


class PagedPanel(QWidget):
    """A paginated modal panel."""

    def __init__(self, size: tuple[int, int], stack: list[PagedPanelState]):
        super().__init__()

        self._stack: list[PagedPanelState] = stack
        self._index: int = 0

        self.setMinimumSize(*size)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setObjectName("baseLayout")
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(12, 12, 12, 12)

        self.title_label = QLabel()
        self.title_label.setObjectName("fieldTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.body_container = QWidget()
        self.body_container.setObjectName("bodyContainer")
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        self.button_nav_container = QWidget()
        self.button_nav_layout = QHBoxLayout(self.button_nav_container)

        self.root_layout.addWidget(self.content_container)
        self.content_layout.addWidget(self.title_label)
        self.content_layout.addWidget(self.body_container)
        self.content_layout.addStretch(1)
        self.root_layout.addWidget(self.button_nav_container)

        self.init_connections()
        self.update_frame()

    def init_connections(self):
        """Initialize button navigation connections."""
        for frame in self._stack:
            for button in frame.connect_to_back:
                button.clicked.connect(self.back)
            for button in frame.connect_to_next:
                button.clicked.connect(self.next)

    def back(self):
        """Navigate backward in the state stack. Close if out of bounds."""
        if self._index > 0:
            self._index = self._index - 1
            self.update_frame()
        else:
            self.close()

    def next(self):
        """Navigate forward in the state stack. Close if out of bounds."""
        if self._index < len(self._stack) - 1:
            self._index = self._index + 1
            self.update_frame()
        else:
            self.close()

    def update_frame(self):
        frame: PagedPanelState = self._stack[self._index]

        # Update Title
        self.setWindowTitle(frame.title)
        self.title_label.setText(f"<h1>{frame.title}</h1>")

        # Update Body Widget
        if self.body_layout.itemAt(0):
            self.body_layout.itemAt(0).widget().setHidden(True)
            self.body_layout.removeWidget(self.body_layout.itemAt(0).widget())
        self.body_layout.addWidget(frame.body_wrapper)
        self.body_layout.itemAt(0).widget().setHidden(False)

        # Update Button Widgets
        while self.button_nav_layout.count():
            if _ := self.button_nav_layout.takeAt(0).widget():
                _.setHidden(True)

        for item in frame.buttons:
            if isinstance(item, QWidget):
                self.button_nav_layout.addWidget(item)
                item.setHidden(False)
            elif isinstance(item, int):
                self.button_nav_layout.addStretch(item)
