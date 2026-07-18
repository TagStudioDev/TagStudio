# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import TYPE_CHECKING, Any, override

import structlog
from PySide6.QtCore import Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QGraphicsOpacityEffect, QVBoxLayout

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.views.panel_modal import PanelWidget
from tagstudio.qt.views.stylesheets.stylesheets import (
    autofill_line_edit_style,
    autofill_line_edit_top_style,
)
from tagstudio.qt.views.suggest_box_view import SuggestBoxView

logger = structlog.get_logger(__name__)

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


def _item_id(item: object) -> int:
    item_id: Any = getattr(item, "id")  # noqa: B009  # pyright: ignore[reportExplicitAny]

    if isinstance(item_id, int):
        return item_id
    else:
        raise AttributeError()


def _item_name(item: object) -> str:
    item_name: Any = getattr(item, "name")  # noqa: B009  # pyright: ignore[reportExplicitAny]

    if isinstance(item_name, str):
        return item_name
    else:
        raise AttributeError()


class SuggestBox[T](PanelWidget):
    item_chosen = Signal(int)
    done = Signal()
    tags_updated = Signal()

    def __init__(
        self, view: SuggestBoxView, exclude: list[int] | None = None, is_chooser: bool = True
    ) -> None:
        super().__init__()
        self.view = view
        self.is_chooser = is_chooser
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.view)
        self._driver: QtDriver | None = None
        self.exclude: list[int] = exclude or []
        self.added: list[int] = exclude or []
        self.create_and_add_button_in_layout: bool = False
        self.limit = 5
        self.shift_held = False

        # Limits
        self._unlimited_limit_item_label: str = "All Items"
        self._limit_items: list[tuple[str, int]] = [
            ("25", 25),
            ("50", 50),
            ("100", 100),
            ("250", 250),
            ("500", 500),
            (self._unlimited_limit_item_label, -1),
        ]
        self._default_limit_index: int = 0
        self._previous_limit_index: int = self._default_limit_index

        # Items
        self._search_results: list[T] = []

        self._create_and_add_button_label_key: str = ""
        self.connect_callbacks()

    def connect_callbacks(self) -> None:
        self.view.search_field.textChanged.connect(self.on_search_query_changed)
        self.view.search_field.editingFinished.connect(self.test_editing_finished)
        self.view.search_field.return_pressed.connect(
            lambda: self.on_search_query_submitted(self.view.search_field.text())
        )
        self.view.search_field.shift_return_pressed.connect(
            lambda: self.on_search_query_submitted(
                self.view.search_field.text(), always_create=True
            )
        )

        self.view.search_field.shift_holding.connect(lambda held: self.on_shift_held(held))

    def on_shift_held(self, held: bool):
        if held:
            self.shift_held = True
            opacity_effect = QGraphicsOpacityEffect(self)
            opacity_effect.setOpacity(0.3)
            if self.view.content_layout.count() > 0:
                self.view.content_layout.itemAt(0).widget().setGraphicsEffect(opacity_effect)
        else:
            self.shift_held = False
            if self.view.content_layout.count() > 0:
                self.view.content_layout.itemAt(0).widget().setGraphicsEffect(None)  # pyright: ignore[reportArgumentType]

    def focus_search_box(self, select_all: bool = False) -> None:
        if not self.isHidden():
            self.view.search_field.setFocus()
        if select_all:
            self.view.search_field.selectAll()

    def clear_search_query(self) -> None:
        self.view.search_field.setText("")

    def get_item_widget(self, index: int, library: Library) -> Any:  # pyright: ignore[reportExplicitAny]
        return self.get_item_widget(index, library)

    def set_driver(self, driver: "QtDriver") -> None:
        self._driver = driver

    def _get_previous_limit(self) -> tuple[str, int]:
        return self._limit_items[self._previous_limit_index]

    def _get_max_limit(self) -> int:
        raise NotImplementedError()

    def on_search_query_changed(self, query: str) -> None:
        self.update_items(query)

    def on_search_query_submitted(self, query: str, always_create: bool = False) -> None:
        # Focus search field if no query
        logger.info("Query submitted")
        if not query:
            self.done.emit()
            self.disappear()
            return
        elif not self.isHidden():
            self.view.search_field.setFocus()

        # Create and add item if no search results
        if (len(self._search_results) <= 0) or always_create:
            self.on_item_create(add_to_entry=True)
        elif self.is_chooser:
            self._on_item_chosen(self._search_results[0])

        self.clear_search_query()
        self.update_items()

    def on_item_create(self, add_to_entry: bool = False) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def on_item_edit(self, item: T) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def _on_item_remove(self, item: T) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def _on_item_chosen(self, item: T) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def _is_excluded(self, item: T) -> bool:
        return _item_id(item) in self.exclude

    def update_items(self, query: str | None = None) -> None:
        """Update the item list given a search query."""
        logger.info("[SearchPanel] Updating items", limit=self.limit)

        # Get results for the search query
        query_lower = "" if not query else query.lower()
        search_results: tuple[list[T], list[T]] = self.search_items(query_lower)

        # Sort and prioritize the results
        direct_results = list({item for item in search_results[0] if not self._is_excluded(item)})
        direct_results.sort(key=lambda item: _item_name(item).lower())

        ancestor_results = list({item for item in search_results[1] if not self._is_excluded(item)})
        ancestor_results.sort(key=lambda item: _item_name(item).lower())

        raw_results = list(direct_results + ancestor_results)
        priority_results: set[T] = set()

        if query and query.strip():
            for raw_item in raw_results:
                if _item_name(raw_item).lower().startswith(query_lower):
                    priority_results.add(raw_item)

        all_results: list[T] = sorted(list(priority_results), key=lambda i: len(_item_name(i))) + [
            item for item in raw_results if item not in priority_results
        ]

        # Target items already added to a selection and move them to the end of the list
        already_added: list[T] = [i for i in all_results if _item_id(i) in self.added]
        for item in already_added:
            if item in all_results:
                all_results.remove(item)
        all_results = all_results + already_added

        if self.limit > 0:
            all_results = all_results[: self.limit]

        self._search_results = all_results
        logger.info("[SearchPanel] Search results", results=self._search_results)

        for i in range(0, self.limit):
            item: T | None = all_results[i] if i < len(all_results) else None
            self.set_item_widget(item=item, index=i)

        if self.view.content_layout.isEmpty():
            self.view.scroll_area.setHidden(True)
            self.view.content_layout.setContentsMargins(0, 0, 0, 0)
            self.view.search_field.setStyleSheet(autofill_line_edit_style())
        else:
            self.view.scroll_area.setHidden(False)
            self.view.content_layout.setContentsMargins(6, 6, 6, 6)
            self.view.search_field.setStyleSheet(autofill_line_edit_top_style())

    def search_items(self, query: str) -> tuple[list[T], list[T]]:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def set_item_widget(self, item: T | None, index: int) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    @override
    def showEvent(self, event: QShowEvent) -> None:
        self.update_items()
        self.on_shift_held(held=False)
        self.clear_search_query()
        return super().showEvent(event)

    def test_editing_finished(self):
        logger.info("Editing finished")
        self.tags_updated.emit()
        if self.view.search_field.text() == "":
            self.done.emit()
            self.disappear()

    def disappear(self):
        self.hide()
        self.view.search_field.setDisabled(True)
        self.on_shift_held(held=False)

    def create_item(self, edit_item_panel: PanelWidget, choose_item: bool = False) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def edit_item(self, edit_item_panel: PanelWidget) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()
