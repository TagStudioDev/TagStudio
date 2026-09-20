# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QScrollArea

logger = structlog.get_logger(__name__)


class HorizontalScrollArea(QScrollArea):
    """A QScrollArea that translates vertical scrolling to horizontal movement."""

    @override
    def wheelEvent(self, arg__1: QtGui.QWheelEvent) -> None:
        angle_y = arg__1.angleDelta().y()
        pixel_y = arg__1.pixelDelta().y()
        if angle_y != 0 or pixel_y != 0:
            translated_event = QtGui.QWheelEvent(
                arg__1.position(),
                arg__1.globalPosition(),
                QtCore.QPoint(pixel_y * -1, 0),
                QtCore.QPoint(angle_y * -1, 0),
                arg__1.buttons(),
                arg__1.modifiers(),
                arg__1.phase(),
                arg__1.inverted(),
            )
            arg__1.accept()
            return super().wheelEvent(translated_event)
        else:
            return super().wheelEvent(arg__1)
