# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path
from typing import override

import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel, QWidget

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.utils.file_opener import FileOpenerHelper

logger = structlog.get_logger(__name__)


class FileOpenerLabel(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the FileOpenerLabel.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        self.filepath: Path | None = None

        super().__init__(parent)

    def set_file_path(self, filepath: Path) -> None:
        """Set the filepath to open.

        Args:
            filepath (Path): The path to the file to open.
        """
        self.filepath = filepath

    @override
    def mousePressEvent(self, ev: QMouseEvent) -> None:
        """Handle mouse press events.

        On a left click, open the file in the default file explorer.
        On a right click, show a context menu.

        Args:
            ev (QMouseEvent): The mouse press event.
        """
        if ev.button() == Qt.MouseButton.LeftButton:
            opener = FileOpenerHelper(unwrap(self.filepath))
            opener.open_explorer()
        elif ev.button() == Qt.MouseButton.RightButton:
            # Show context menu
            pass
        else:
            super().mousePressEvent(ev)
