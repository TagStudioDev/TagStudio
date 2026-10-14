# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from collections.abc import Callable
from typing import override

from PySide6.QtCore import QPoint, QRect, QSize, Signal
from PySide6.QtWidgets import QLayout, QLayoutItem, QScrollArea, QWidget

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.views.styles.stylesheets import PAD


class ThumbGridLayout[W: QWidget](QLayout):
    """A recycling scrollable grid for widgets of the a uniform size."""

    _BUFFER_ROWS = 3

    first_visible_changed = Signal(int)  # Index of the first visible item
    items_assigned = Signal(object)  # list[tuple[int, W]] of newly assigned (index, widget) pairs
    items_unassigned = Signal(object)  # list[W] of widgets that no longer have an index

    def __init__(self, scroll_area: QScrollArea, create_widget: Callable[[], W]) -> None:
        super().__init__(None)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(PAD)

        self._assigned: dict[int, W] = {}
        self._create_widget = create_widget
        self._first_visible: int | None = None
        self._free: list[W] = []
        self._item_count = 0
        self._items: list[QLayoutItem] = []
        # [start, end, per_row, item size]
        self._last_layout: tuple[int, int, int, QSize] | None = None
        # Widgets by [row from the first visible row, column] from before the items were replaced
        self._previous_slots: dict[tuple[int, int], W] = {}
        self._previous_offset = 0
        self._scroll_area = scroll_area
        self._scroll_to: int | None = None

    def set_item_count(self, count: int) -> None:
        """Replace all items with `count` new ones, keeping widgets in place if nothing scrolls."""
        self._item_count = count
        if self._assigned:
            self._previous_slots = self._screen_slots()
            self._previous_offset = self._scroll_area.verticalScrollBar().value()
            self._assigned.clear()
        self._first_visible = None
        self._last_layout = None
        self.update()

    def scroll_to_index(self, index: int) -> None:
        self._scroll_to = index
        self.update()

    def ensure_visible(self, index: int, bottom_padding: int = 0) -> None:
        """Scroll just enough to fully show the item at `index` above `bottom_padding` pixels."""
        per_row, cell = self._grid_metrics(self.geometry().width())
        top = index // per_row * cell.height() - self.spacing()
        bottom = top + self._item_size().height() + 2 * self.spacing()
        scroll_bar = self._scroll_area.verticalScrollBar()
        visible_height = self._scroll_area.viewport().height() - bottom_padding
        if top < scroll_bar.value():
            scroll_bar.setValue(top)
        elif bottom > scroll_bar.value() + visible_height:
            scroll_bar.setValue(bottom - visible_height)

    def items_per_row(self) -> int:
        return self._grid_metrics(self.geometry().width())[0]

    def first_visible_index(self) -> int | None:
        return self._first_visible

    def widget_at(self, index: int) -> W | None:
        return self._assigned.get(index)

    def assigned_items(self) -> list[tuple[int, W]]:
        return sorted(self._assigned.items(), key=lambda item: item[0])

    def widgets(self) -> list[W]:
        return [*self._assigned.values(), *self._previous_slots.values(), *self._free]

    def _screen_slots(self) -> dict[tuple[int, int], W]:
        """Assigned widgets by their row from the first visible row and their column."""
        per_row = unwrap(self._last_layout)[2]
        first_row = unwrap(self._first_visible) // per_row
        return {
            (index // per_row - first_row, index % per_row): widget
            for index, widget in self._assigned.items()
        }

    def _new_widget(self) -> W:
        widget = self._create_widget()
        self.addWidget(widget)
        return widget

    def _item_size(self) -> QSize:
        """The first widget's size hint within its size limits, even before it's been shown."""
        if not self._items:
            self._free.append(self._new_widget())
        widget = unwrap(self._items[0].widget())
        return widget.sizeHint().expandedTo(widget.minimumSize()).boundedTo(widget.maximumSize())

    def _grid_metrics(self, width: int) -> tuple[int, QSize]:
        """Return how many items fit in a row, and the size of each item's cell."""
        size = self._item_size()
        cell = QSize(size.width() + self.spacing(), size.height() + self.spacing())
        return max(1, int(width / cell.width())), cell

    @override
    def setGeometry(self, arg__1: QRect) -> None:
        super().setGeometry(arg__1)
        if self._item_count == 0:
            unassigned = [*self._assigned.values(), *self._previous_slots.values()]
            self._assigned.clear()
            self._previous_slots.clear()
            self._free.extend(unassigned)
            for widget in self._free:
                widget.setGeometry(32_000, 32_000, 0, 0)
            if unassigned:
                self.items_unassigned.emit(unassigned)
            return

        per_row, cell = self._grid_metrics(arg__1.width())
        scroll_bar = self._scroll_area.verticalScrollBar()
        if self._scroll_to is not None:
            viewport_height = self._scroll_area.viewport().height()
            maximum = max(0, self.totalHeightForWidth(arg__1.width()) - viewport_height)
            scroll_bar.setMaximum(maximum)
            scroll_bar.setValue(min((self._scroll_to // per_row) * cell.height(), maximum))
            self._scroll_to = None

        offset = scroll_bar.value()
        unassigned: list[W] = []
        if offset != self._previous_offset:
            unassigned.extend(self._previous_slots.values())
            self._free.extend(self._previous_slots.values())
            self._previous_slots.clear()
        last_row = (self._item_count - 1) // per_row
        first_row = min(offset // cell.height(), last_row)
        visible_rows = math.ceil(
            (self._scroll_area.viewport().height() + offset % cell.height()) / cell.height()
        )

        first_visible = first_row * per_row
        if first_visible != self._first_visible:
            self._first_visible = first_visible
            self.first_visible_changed.emit(first_visible)

        start = max(0, (first_row - self._BUFFER_ROWS) * per_row)
        end = min(self._item_count, (first_row + visible_rows + self._BUFFER_ROWS) * per_row)
        item_size = self._item_size()
        if (start, end, per_row, item_size) == self._last_layout:
            return
        self._last_layout = (start, end, per_row, item_size)

        moved_out = [
            self._assigned.pop(index) for index in list(self._assigned) if not start <= index < end
        ]
        self._free.extend(moved_out)
        unassigned.extend(moved_out)

        newly_assigned: list[tuple[int, W]] = []
        for index in range(start, end):
            widget = self._assigned.get(index)
            row, column = divmod(index, per_row)
            if widget is None:
                widget = self._previous_slots.pop((row - first_row, column), None)
                if widget is None:
                    widget = self._free.pop() if self._free else self._new_widget()
                self._assigned[index] = widget
                newly_assigned.append((index, widget))
            widget.setGeometry(QRect(QPoint(column * cell.width(), row * cell.height()), item_size))

        unassigned.extend(self._previous_slots.values())
        self._free.extend(self._previous_slots.values())
        self._previous_slots.clear()
        for widget in self._free:
            widget.setGeometry(32_000, 32_000, 0, 0)

        if unassigned:
            self.items_unassigned.emit(unassigned)
        if newly_assigned:
            self.items_assigned.emit(newly_assigned)

    @override
    def addItem(self, arg__1: QLayoutItem) -> None:
        self._items.append(arg__1)

    @override
    def count(self) -> int:
        return len(self._items)

    @override
    def itemAt(self, index: int) -> QLayoutItem:
        if not 0 <= index < len(self._items):
            return None  # pyright: ignore[reportReturnType]
        return self._items[index]

    @override
    def takeAt(self, index: int) -> QLayoutItem:
        if not 0 <= index < len(self._items):
            return None  # pyright: ignore[reportReturnType]
        item = self._items.pop(index)
        widget = item.widget()
        self._free = [w for w in self._free if w is not widget]
        self._assigned = {i: w for i, w in self._assigned.items() if w is not widget}
        self._previous_slots = {k: w for k, w in self._previous_slots.items() if w is not widget}
        return item

    @override
    def hasHeightForWidth(self) -> bool:
        return True

    @override
    def heightForWidth(self, arg__1: int) -> int:
        if self._item_count == 0:
            return 0
        per_row, cell = self._grid_metrics(arg__1)
        return math.ceil(self._item_count / per_row) * cell.height()

    @override
    def sizeHint(self) -> QSize:
        if not self._items:
            return QSize()
        return self._item_size()
