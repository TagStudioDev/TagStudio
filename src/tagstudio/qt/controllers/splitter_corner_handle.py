# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from enum import Enum, auto
from typing import cast, override

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import (
    QColor,
    QEnterEvent,
    QGuiApplication,
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
from tagstudio.qt.views.styles.stylesheets import (
    RADIUS,
    RESIZE_HANDLE_LENGTH,
    RESIZE_HANDLE_WIDTH,
    is_dark_theme,
    item_thumb_hover_color,
)
from tagstudio.qt.views.styles.tagstudio_style import set_handles_hidden

_REST_COLOR = QColor(210, 210, 210)
_LIGHT_REST_COLOR = QColor(170, 170, 170)
_OUTLINE_COLOR = QColor(0, 0, 0, 64)
_OUTLINE_WIDTH = 1


class _Part(Enum):
    BRACKET = auto()
    LINE = auto()


class SplitterCornerHandle(QWidget):
    """A corner handle that moves two splitters at once."""

    # Sides are slightly shorter than a full handle for visual balance
    _BRACKET_SIDE_LENGTH = RESIZE_HANDLE_LENGTH - (RESIZE_HANDLE_WIDTH * 2)
    _GRAB_AREA_WIDTH = 18

    def __init__(
        self,
        outer_splitter: QSplitter,
        inner_splitter: QSplitter,
        content_widget: Callable[[], QWidget | None],
        parent: QWidget,
    ) -> None:
        super().__init__(parent)
        self._bracket_region = QRegion()
        self._collapsible: list[tuple[QSplitter, int, bool]] = []
        self._content_widget = content_widget
        self._corner = QPointF()
        self._drag_part: _Part | None = None
        self._drag_start: tuple[QPointF, int, int] | None = None
        self._hovered_part: _Part | None = None
        self._inner_splitter = inner_splitter
        self._is_hovered = False
        self._is_inner_handle_down = False
        self._is_painted_revealed = False
        self._line_center = QPointF()
        self._line_region = QRegion()
        self._outer_splitter = outer_splitter
        self._painted_limits = (False, False)
        self._parent = parent
        self._watched: set[QWidget] = set()

        self.setMouseTracking(True)
        set_handles_hidden(inner_splitter, hidden=True)
        outer_splitter.splitterMoved.connect(self.queue_update)
        inner_splitter.splitterMoved.connect(self.queue_update)
        widget: QWidget | None = inner_splitter
        while widget is not None and widget is not parent:
            self._watch(widget)
            widget = widget.parentWidget()
        self._watch(inner_splitter.handle(1))
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

    def _shown_content_widget(self) -> QWidget | None:
        """The content widget, if it's shown."""
        content_widget = self._content_widget()
        if content_widget is None or content_widget.visibleRegion().isEmpty():
            return None
        return content_widget

    def _is_revealed(self) -> bool:
        """Whether the handles show."""
        content_widget = self._shown_content_widget()
        # NOTE: The media player's underMouse() also shows its controls, so read the flag here
        return content_widget is not None and (
            self._drag_start is not None
            or self._is_inner_handle_down
            or self._is_hovered
            or content_widget.testAttribute(Qt.WidgetAttribute.WA_UnderMouse)
            or self._inner_splitter.handle(1).underMouse()
        )

    def queue_update(self) -> None:
        """Schedule an update of these handles' position and visibility."""
        # NOTE: Queuing lets Qt drop requests made while one is already pending.
        QCoreApplication.postEvent(self, QEvent(QEvent.Type.LayoutRequest))

    @override
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.LayoutRequest:
            self._update_geometry()
            return True
        return super().event(event)

    def _update_geometry(self) -> None:
        # NOTE: The release can miss the handle if its panel hides mid-press
        if (
            self._is_inner_handle_down
            and not QGuiApplication.mouseButtons() & Qt.MouseButton.LeftButton
        ):
            self._is_inner_handle_down = False
            self.update()

        # Only repaint when handles show or hide so the media player isn't redrawing too much
        if self._is_revealed() != self._is_painted_revealed:
            self.update()

        content_widget = self._shown_content_widget()
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
        grab = self._GRAB_AREA_WIDTH
        side = self._BRACKET_SIDE_LENGTH
        bottom = content_rect.y() + content_rect.height()
        area = QRect(
            content_rect.x() - grab // 2,
            bottom - side - grab // 2,
            content_rect.width() + grab,
            side + grab,
        )
        self.setGeometry(area)

        corner_x = content_rect.x() if direction > 0 else content_rect.x() + content_rect.width()
        self._corner = QPointF(corner_x - area.x(), bottom - area.y())
        line_x = content_rect.x() + content_rect.width() / 2 - area.x()
        self._line_center = QPointF(line_x, self._corner.y())

        # Mask the grab areas so the content between them can still be clicked
        corner = self._corner.toPoint()
        bracket_left = corner.x() - grab // 2 if direction > 0 else corner.x() - side - grab // 2
        self._bracket_region = QRegion(corner.x() - grab // 2, 0, grab, self.height()).united(
            QRegion(bracket_left, corner.y() - grab // 2, side + grab, grab)
        )
        line_left = round(self._line_center.x() - RESIZE_HANDLE_LENGTH / 2) - grab // 2
        self._line_region = QRegion(
            line_left, corner.y() - grab // 2, RESIZE_HANDLE_LENGTH + grab, grab
        )
        self.setMask(self._bracket_region.united(self._line_region))
        self.show()
        self.raise_()

    def _part_at(self, position: QPoint) -> _Part | None:
        if self._bracket_region.contains(position):
            return _Part.BRACKET
        if self._line_region.contains(position):
            return _Part.LINE
        return None

    def _update_cursor(self) -> None:
        _, direction = self._outer_handle()
        if self._hovered_part == _Part.LINE:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(
                Qt.CursorShape.SizeBDiagCursor if direction > 0 else Qt.CursorShape.SizeFDiagCursor
            )

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (
            QEvent.Type.Move,
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.Hide,
            QEvent.Type.Enter,
            QEvent.Type.Leave,
        ):
            self.queue_update()
        if event.type() in (
            QEvent.Type.Enter,
            QEvent.Type.Leave,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
        ) and watched is self._inner_splitter.handle(1):
            if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
                self._is_inner_handle_down = event.type() == QEvent.Type.MouseButtonPress
            self.update()
        return super().eventFilter(watched, event)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self._is_hovered = True
        self._hovered_part = self._part_at(event.position().toPoint())
        self._update_cursor()
        self.update()
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self._is_hovered = False
        self._hovered_part = None
        self.update()
        super().leaveEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        part = self._part_at(event.position().toPoint())
        if event.button() != Qt.MouseButton.LeftButton or part is None:
            super().mousePressEvent(event)
            return
        handle_index, _ = self._outer_handle()
        self._drag_part = part
        self._drag_start = (
            event.globalPosition(),
            self._outer_splitter.handle(handle_index).x(),
            self._inner_splitter.handle(1).y(),
        )
        if part == _Part.BRACKET:
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
            part = self._part_at(event.position().toPoint())
            if part != self._hovered_part:
                self._hovered_part = part
                self._update_cursor()
                self.update()
            super().mouseMoveEvent(event)
            return
        press, outer_start, inner_start = self._drag_start
        delta = (event.globalPosition() - press).toPoint()
        handle_index, _ = self._outer_handle()
        outer_handle = self._outer_splitter.handle(handle_index)
        inner_handle = self._inner_splitter.handle(1)
        if self._drag_part == _Part.BRACKET:
            outer_position = outer_start + delta.x()
            if outer_position != outer_handle.x():
                self._outer_splitter.moveSplitter(outer_position, handle_index)
        inner_position = inner_start + delta.y()
        if inner_position != inner_handle.y():
            self._inner_splitter.moveSplitter(inner_position, 1)
        if self._limits() != self._painted_limits:
            self.update()

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_start = None
        self._drag_part = None
        for splitter, index, collapsible in self._collapsible:
            splitter.setCollapsible(index, collapsible)
        self._collapsible = []
        self.update()
        super().mouseReleaseEvent(event)

    def _limits(self) -> tuple[bool, bool]:
        """Whether the panel or its content is at its largest, and if the splitter is at a limit."""
        handle_index, direction = self._outer_handle()
        outer_lowest, outer_highest = cast(
            tuple[int, int], self._outer_splitter.getRange(handle_index)
        )
        outer_position = self._outer_splitter.handle(handle_index).x()
        is_widest = (
            outer_position <= outer_lowest if direction > 0 else outer_position >= outer_highest
        )
        is_line_at_limit = bool(self._inner_splitter.property("at_limit"))
        inner_lowest, _ = cast(tuple[int, int], self._inner_splitter.getRange(1))
        is_tallest = is_line_at_limit and self._inner_splitter.handle(1).y() > inner_lowest
        return is_widest or is_tallest, is_line_at_limit

    def _part_color(self, part: _Part, is_down: bool, is_at_limit: bool) -> QColor:
        if is_down:
            return Palette.contrast() if is_at_limit else Palette.accent_alt()
        if self._hovered_part == part:
            return item_thumb_hover_color()
        return _REST_COLOR if is_dark_theme() else _LIGHT_REST_COLOR

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        self._is_painted_revealed = self._is_revealed()
        if not self._is_painted_revealed:
            return
        _, direction = self._outer_handle()
        self._painted_limits = self._limits()
        is_at_largest, is_line_at_limit = self._painted_limits
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bracket_color = self._part_color(
            _Part.BRACKET, self._drag_part == _Part.BRACKET, is_at_largest
        )
        corner = self._corner
        side = self._BRACKET_SIDE_LENGTH
        path = QPainterPath(corner - QPointF(0, side))
        path.lineTo(corner - QPointF(0, RADIUS))
        path.quadTo(corner, corner + QPointF(direction * RADIUS, 0))
        path.lineTo(corner + QPointF(direction * side, 0))
        self._stroke_outlined(painter, path, bracket_color)

        is_line_down = self._drag_part == _Part.LINE or self._is_inner_handle_down
        line_color = self._part_color(_Part.LINE, is_line_down, is_line_at_limit)
        if not is_line_down and self._inner_splitter.handle(1).underMouse():
            line_color = item_thumb_hover_color()
        half_length = RESIZE_HANDLE_LENGTH / 2
        line = QPainterPath(self._line_center - QPointF(half_length, 0))
        line.lineTo(self._line_center + QPointF(half_length, 0))
        self._stroke_outlined(painter, line, line_color)

    @staticmethod
    def _stroke_outlined(painter: QPainter, path: QPainterPath, color: QColor) -> None:
        """Stroke a handle over a dark outline."""
        pen = QPen(_OUTLINE_COLOR, RESIZE_HANDLE_WIDTH + _OUTLINE_WIDTH * 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)
        pen.setColor(color)
        pen.setWidthF(RESIZE_HANDLE_WIDTH)
        painter.setPen(pen)
        painter.drawPath(path)
