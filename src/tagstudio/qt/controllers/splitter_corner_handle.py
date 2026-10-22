# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from typing import override

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import (
    QEnterEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QRegion,
)
from PySide6.QtWidgets import QSplitter, QWidget

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.views.styles.palette import Palette
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, RADIUS


class SplitterCornerHandle(QWidget):
    """A corner handle on a side panel's content that moves the panel's two splitters at once."""

    _BRACKET_SIDE_LENGTH = 18
    _BRACKET_WIDTH = 3
    _BRACKET_OFFSET = HALF_PAD + _BRACKET_WIDTH / 2
    _GRAB_AREA_WIDTH = 18  # Invisible grab area width

    def __init__(
        self,
        outer_splitter: QSplitter,
        inner_splitter: QSplitter,
        content_widget: Callable[[], QWidget | None],
        parent: QWidget,
        snap_outer: Callable[[int], int] | None = None,
    ) -> None:
        super().__init__(parent)
        self._parent = parent
        self._outer_splitter = outer_splitter
        self._inner_splitter = inner_splitter
        self._content_widget = content_widget
        self._snap_outer = snap_outer
        self._watched: set[QWidget] = set()
        self._is_hovered = False
        self._corner = QPointF()
        self._drag_start: tuple[QPointF, int, int] | None = None
        self._collapsible: list[tuple[QSplitter, int, bool]] = []

        size = self._GRAB_AREA_WIDTH // 2 + self._BRACKET_SIDE_LENGTH + self._BRACKET_WIDTH
        self.resize(size, size)

        outer_splitter.splitterMoved.connect(self.queue_update)
        inner_splitter.splitterMoved.connect(self.queue_update)
        widget: QWidget | None = inner_splitter
        while widget is not None and widget is not parent:
            self._watch(widget)
            widget = widget.parentWidget()
        self.queue_update()

    def _watch(self, widget: QWidget) -> None:
        if widget not in self._watched:
            widget.installEventFilter(self)
            self._watched.add(widget)

    def _outer_handle(self) -> tuple[int, int]:
        """The outer handle beside the panel, and 1 if the panel is to its right or -1 if left."""
        panel = next(
            i
            for i in range(self._outer_splitter.count())
            if unwrap(self._outer_splitter.widget(i)).isAncestorOf(self._inner_splitter)
        )
        return (panel, 1) if panel > 0 else (1, -1)

    def _vertex(self, direction: int) -> QPoint:
        """Where the grab strips cross in this widget's coordinates."""
        inset = self._GRAB_AREA_WIDTH // 2
        x = inset if direction > 0 else self.width() - inset
        return QPoint(x, self.height() - inset)

    def queue_update(self) -> None:
        """Schedule an update of this handle's position and visibility."""
        # NOTE: Queuing lets Qt drop requests made while one is already pending.
        QCoreApplication.postEvent(self, QEvent(QEvent.Type.LayoutRequest))

    @override
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.LayoutRequest:
            self._update_geometry()
            return True
        return super().event(event)

    def _update_geometry(self) -> None:
        content_widget = self._content_widget()
        handle_index, direction = self._outer_handle()
        if (
            content_widget is None
            or not self._outer_splitter.handle(handle_index).isVisible()
            or self._inner_splitter.width() == 0
        ):
            self.hide()
            return
        self._watch(content_widget)

        content_rect = QRect(
            content_widget.mapTo(self._parent, QPoint(0, 0)), content_widget.size()
        )
        gap = self._BRACKET_OFFSET
        corner_x = (
            content_rect.x() - gap
            if direction > 0
            else content_rect.x() + content_rect.width() + gap
        )
        self._corner = QPointF(corner_x, content_rect.y() + content_rect.height() + gap)
        vertex = self._vertex(direction)
        self.move((self._corner - vertex).toPoint())

        # Masks the grabbable area to roughly the handle area, so the empty space in front of the
        # content can be clicked through and doesn't intercept the grab.
        grab = self._GRAB_AREA_WIDTH
        mask = QRegion(vertex.x() - grab // 2, 0, grab, self.height())
        mask = mask.united(QRegion(0, vertex.y() - grab // 2, self.width(), grab))
        self.setMask(mask)

        self.setCursor(
            Qt.CursorShape.SizeBDiagCursor if direction > 0 else Qt.CursorShape.SizeFDiagCursor
        )
        self.show()
        self.raise_()

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (
            QEvent.Type.Move,
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.Hide,
        ):
            self.queue_update()
        if (
            event.type() in (QEvent.Type.Enter, QEvent.Type.Leave)
            and watched is self._content_widget()
        ):
            self.update()
        return super().eventFilter(watched, event)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        handle_index, _ = self._outer_handle()
        self._drag_start = (
            event.globalPosition(),
            self._outer_splitter.handle(handle_index).x(),
            self._inner_splitter.handle(1).y(),
        )
        # Don't allow panel to be closed by the corner handle, it's weird otherwise.
        self._collapsible = [
            (splitter, index, splitter.isCollapsible(index))
            for splitter in (self._outer_splitter, self._inner_splitter)
            for index in range(splitter.count())
        ]
        for splitter, index, _ in self._collapsible:
            splitter.setCollapsible(index, False)  # noqa: FBT003
        self.update()

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is None:
            super().mouseMoveEvent(event)
            return
        press, outer_start, inner_start = self._drag_start
        delta = (event.globalPosition() - press).toPoint()
        handle_index, _ = self._outer_handle()
        outer_position = outer_start + delta.x()
        if self._snap_outer is not None:
            outer_position = self._snap_outer(outer_position)
        if outer_position != self._outer_splitter.handle(handle_index).x():
            self._outer_splitter.moveSplitter(outer_position, handle_index)
        inner_position = inner_start + delta.y()
        if inner_position != self._inner_splitter.handle(1).y():
            self._inner_splitter.moveSplitter(inner_position, 1)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_start = None
        for splitter, index, collapsible in self._collapsible:
            splitter.setCollapsible(index, collapsible)
        self._collapsible = []
        self.update()
        super().mouseReleaseEvent(event)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        content_widget = self._content_widget()
        is_content_hovered = content_widget is not None and content_widget.underMouse()
        if not (self._is_hovered or is_content_hovered or self._drag_start is not None):
            return
        _, direction = self._outer_handle()
        vertex = self._corner - QPointF(self.pos())
        radius = RADIUS + self._BRACKET_OFFSET
        side = self._BRACKET_SIDE_LENGTH

        path = QPainterPath(vertex - QPointF(0, side))
        path.lineTo(vertex - QPointF(0, radius))
        path.quadTo(vertex, vertex + QPointF(direction * radius, 0))
        path.lineTo(vertex + QPointF(direction * side, 0))

        pen = QPen(Palette.accent(), self._BRACKET_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        painter.drawPath(path)
