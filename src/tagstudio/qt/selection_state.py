# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable, Hashable, Iterable, Sequence

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
        self._selection_cursor: T | None = None  # Where the last click or arrow key moved to

    @property
    def selected(self) -> list[T]:
        return list(self._selected)

    @property
    def cursor(self) -> T | None:
        return self._selection_cursor

    def is_selected(self, item_id: T) -> bool:
        return item_id in self._selected

    def toggle_item_selection(self, item_id: T, append: bool, bridge: bool) -> None:
        """Toggle the selection of an item.

        If an item is not selected, this selects it. If an item is already selected, this will
        deselect it as long as append is `True` and bridge is `False`.

        Args:
            item_id(T): The ID of the item/entry to select.
            append(bool): Whether or not to add this item to the previous selection
                or to restart the selection with this item.
                Setting to `True` acts like "Ctrl + Click" selecting.
            bridge(bool): Whether or not to select items in the visual range of the anchor and
                this current item. The anchor is the last item selected without bridge,
                or the latest selected item if that one gets deselected.
                Setting to `True` acts like "Shift + Click" selecting,
                or like "Ctrl + Shift + Click" when append is also `True`.
        """
        logger.info(
            "[SelectionState] Selecting Items:", item_id=item_id, append=append, bridge=bridge
        )
        order = self._order()
        if bridge and self._selection_anchor in order:
            self._existing_selection = self.selected if append else []
            self._select_range(order, order.index(item_id))
        else:
            if not append:
                self._selected = {item_id: None}
            elif item_id in self._selected and not bridge:
                self._selected.pop(item_id)
            else:
                self._selected[item_id] = None
            self._selection_anchor = item_id
            self._selection_cursor = item_id
            self._keep_anchor_selected()
            self._existing_selection = self.selected
        self.changed.emit()

    def select_all(self) -> None:
        """Set the selection to all items in the results."""
        self._selected = dict.fromkeys(self._order())
        self._existing_selection = self.selected
        self.changed.emit()

    def select_inverse(self) -> None:
        """Invert the selection of all items in the results."""
        self._selected = {item: None for item in self._order() if item not in self._selected}
        self._keep_anchor_selected()
        self._existing_selection = self.selected
        self.changed.emit()

    def clear(self) -> None:
        self._selected = {}
        self._existing_selection = []
        self._selection_anchor = None
        self._selection_cursor = None
        self.changed.emit()

    def deselect(self, item_ids: Iterable[T]) -> None:
        removed = self._selected.keys() & set(item_ids)
        if not removed:
            return
        self._selected = {item: None for item in self._selected if item not in removed}
        self._existing_selection = [i for i in self._existing_selection if i not in removed]
        self._keep_anchor_selected()
        if self._selection_cursor in removed:
            self._selection_cursor = self._selection_anchor
        self.changed.emit()

    def move_selection(self, order: Sequence[T], target: int, extend: bool) -> int:
        """Move or extend the selection to `order[target]`, like with an arrow key.

        Returns:
            int: The index in `order` the selection moved to.
        """
        cursor = self._selection_cursor
        index = order.index(cursor) if cursor in order else None
        if not extend:
            self._selection_anchor = order[target]
            self._existing_selection = []
        elif self._selection_anchor not in order:
            # Keep existing items selected and start a new range here
            self._selection_anchor = order[target]
            self._existing_selection = self.selected
        elif index is not None and target != index:
            # Skip past an earlier selection instead of stopping inside it
            # NOTE: This mimics macOS Finder behavior in list view
            direction = 1 if target > index else -1
            earlier = set(self._existing_selection)
            while 0 <= target < len(order) and order[target] in earlier:
                target += direction
            if not 0 <= target < len(order):  # The earlier selection reaches the edge
                target -= direction

        previous = self.selected
        self._select_range(order, target)
        if self.selected != previous:
            self.changed.emit()
        return target

    def _keep_anchor_selected(self) -> None:
        """Move the anchor and cursor to the latest selected item if the anchor isn't selected.

        NOTE: This mimics macOS Finder's list view behavior, rather than Windows Explorer which
        keeps the anchor around after it's deselected.
        """
        if self._selection_anchor not in self._selected:
            self._selection_anchor = next(reversed(self._selected), None)
            self._selection_cursor = self._selection_anchor

    def _select_range(self, order: Sequence[T], target: int) -> None:
        """Select the existing selection plus the items from the anchor to `order[target]`."""
        anchor = order.index(self._selection_anchor)
        step = 1 if target >= anchor else -1
        self._selection_cursor = order[target]
        span = [order[i] for i in range(anchor, target + step, step)]
        in_span = set(span)
        self._existing_selection = [i for i in self._existing_selection if i not in in_span]
        self._selected = dict.fromkeys(self._existing_selection + span)
