# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path
from typing import override

import structlog
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent, QFont, QMouseEvent, QResizeEvent
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

from tagstudio.qt.utils.file_opener import FileOpenerHelper

logger = structlog.get_logger(__name__)


class FileOpenerLabel(QLabel):
    """A file's name that opens the file when clicked."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.filepath: Path | None = None
        self._name = ""
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        font = self.font()
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)

    def set_file_path(self, filepath: Path) -> None:
        """Set the file to name and open."""
        self.filepath = filepath
        self._name = filepath.name
        self.setToolTip(self._name)
        self._fit_name()

    def _fit_name(self) -> None:
        self.setText(
            self.fontMetrics().elidedText(self._name, Qt.TextElideMode.ElideMiddle, self.width())
        )

    def _set_underlined(self, underlined: bool) -> None:
        font = self.font()
        font.setUnderline(underlined)
        self.setFont(font)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._fit_name()

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self._set_underlined(underlined=True)
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self._set_underlined(underlined=False)
        super().leaveEvent(event)

    @override
    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if ev.button() == Qt.MouseButton.LeftButton and self.filepath is not None:
            FileOpenerHelper(self.filepath).open_file()
        else:
            super().mousePressEvent(ev)
