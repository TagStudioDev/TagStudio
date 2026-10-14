# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable, Hashable, Sequence

import structlog
from PySide6.QtCore import QObject, Signal

logger = structlog.get_logger(__name__)


class SelectionState[T: Hashable](QObject):
    """Tracks which items are selected, emitting `changed` whenever the selection changes."""

    changed = Signal()

    def __init__(self, order: Callable[[], Sequence[T]]) -> None:
        """Track the selection of the items from `order`, which returns them in the shown order."""
        super().__init__()
        self._existing_selection: list[T] = []
        self._order = order
        self._selected: dict[T, None] = {}
        self._selection_anchor: T | None = None
        self._selection_cursor: T | None = None  # Where the arrow keys last moved to

    @property
    def selected(self) -> list[T]:
        return list(self._selected)

    @property
    def last_selected(self) -> T | None:
        return next(reversed(self._selected), None)

    def is_selected(self, item_id: T) -> bool:
        return item_id in self._selected

    def toggle_item_selection(self, item_id: T, append: bool, bridge: bool) -> None:
        """Toggle the selection of an item.

        If an item is not selected, this selects it. If an item is already selected, this will
        deselect it as long as append and bridge are False.

        Args:
            item_id(T): The ID of the item/entry to select.
            append(bool): Whether or not to add this item to the previous selection
                or to restart the selection with this item.
                Setting to True acts like "Ctrl + Click" selecting.
            bridge(bool): Whether or not to select items in the visual range of the last item
                selected and this current item.
                Setting to True acts like "Shift + Click" selecting.
        """
        logger.info(
            "[SelectionState] Selecting Items:", item_id=item_id, append=append, bridge=bridge
        )
        if append:
            self._select_item(item_id)
        elif bridge:
            self._select_to_item(item_id)
        else:
            self._selected = {item_id: None}
        self.changed.emit()

    def select_all(self) -> None:
        """Set the selection to all items in the results."""
        self._selected = dict.fromkeys(self._order())
        self.changed.emit()

    def select_inverse(self) -> None:
        """Invert the selection of all items in the results."""
        self._selected = {item: None for item in self._order() if item not in self._selected}
        self.changed.emit()

    def clear(self) -> None:
        self._selected = {}
        self.changed.emit()

    def move_selection(self, order: Sequence[T], target: int, extend: bool) -> int:
        """Move or extend the selection to `order[target]`, like with an arrow key.

        Returns:
            int: The index in `order` the selection moved to.
        """
        cursor = self.last_selected
        if cursor != self._selection_cursor:  # The selection was changed somewhere else
            self._selection_anchor = cursor
            self._existing_selection = self.selected
        index = order.index(cursor) if cursor in order else None
        if not extend or self._selection_anchor not in order:
            self._selection_anchor = order[target]
            self._existing_selection = []
        elif index is not None and target != index:
            # Skip past an earlier selection instead of stopping inside it
            # NOTE: This mimics macOS Finder behavior in list view
            direction = 1 if target > index else -1
            earlier = set(self._existing_selection)
            while 0 <= target < len(order) and order[target] in earlier:
                target += direction
            if not 0 <= target < len(order):  # The earlier selection reaches the edge
                target -= direction

        anchor = order.index(self._selection_anchor)
        step = 1 if target >= anchor else -1
        self._selection_cursor = order[target]
        span = [order[i] for i in range(anchor, target + step, step)]
        in_span = set(span)
        self._existing_selection = [i for i in self._existing_selection if i not in in_span]
        selected = dict.fromkeys(self._existing_selection + span)
        if list(selected) != self.selected:
            self._selected = selected
            self.changed.emit()
        return target

    def _select_item(self, item_id: T) -> None:
        if item_id in self._selected:
            self._selected.pop(item_id)
        else:
            self._selected[item_id] = None

    def _select_to_item(self, item_id: T) -> None:
        if len(self._selected) == 0:
            self._select_item(item_id)
            return
        order = self._order()
        start = order.index(self.last_selected)
        end = order.index(item_id)

        if start > end:
            end, start = start, end
        else:
            end += 1

        for i in range(start, end):
            self._selected[order[i]] = None
