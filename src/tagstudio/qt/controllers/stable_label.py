# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QLabel, QWidget


class StableLabel(QLabel):
    """A QLabel that resists "jiggling" from rapidly changing text.

    Holds its `sizeHint()` width at the widest shown since the last reset_width() call,
    and is always kept left aligned of that, so a centering layout's box stops
    growing/shrinking on every update (aka the "jiggle" effect).
    """

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._min_width = 0

    def reset_width(self) -> None:
        """Let the tracked width shrink again, for new unrelated text."""
        self._min_width = 0
        self.updateGeometry()

    @override
    def setText(self, text: str) -> None:
        super().setText(text)
        self._min_width = max(self._min_width, super().sizeHint().width())
        self.updateGeometry()

    @override
    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        return QSize(max(hint.width(), self._min_width), hint.height())
