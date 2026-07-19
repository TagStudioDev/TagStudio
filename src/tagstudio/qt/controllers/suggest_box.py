# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import TYPE_CHECKING, Any, override

import structlog
from PySide6.QtCore import Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.controllers.autofill_line_edit import QtCore, QtGui
from tagstudio.qt.views.panel_modal import PanelWidget
from tagstudio.qt.views.stylesheets.stylesheets import (
    autofill_line_edit_style,
    autofill_line_edit_top_style,
)
from tagstudio.qt.views.suggest_box_view import SuggestBoxView

logger = structlog.get_logger(__name__)

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


class SuggestBox[T](QWidget):
    item_chosen = Signal(object)
    done = Signal()

    def __init__(self, driver: "QtDriver", view: SuggestBoxView) -> None:
        super().__init__()
        self._layout = view
        self._driver = driver
        self._limit = 5
        self._is_shift_held = False
        self._search_results: list[T] = []
        self.added: list[int] = []
        self.excluded: list[int] = []

        self.setLayout(self._layout)
        self._connect_callbacks()

    def hide_and_reset(self):
        self.hide()
        self._layout.search_field.setDisabled(True)
        self._on_shift_held(held=False)

    def _connect_callbacks(self) -> None:
        self._layout.search_field.textChanged.connect(self._on_search_query_changed)
        self._layout.search_field.editingFinished.connect(self._editing_finished_callback)
        self._layout.search_field.return_pressed.connect(
            lambda: self._on_search_query_submitted(self._layout.search_field.text())
        )
        self._layout.search_field.shift_return_pressed.connect(
            lambda: self._on_search_query_submitted(
                self._layout.search_field.text(), always_create=True
            )
        )

        self._layout.search_field.shift_holding.connect(lambda held: self._on_shift_held(held))

    def _on_shift_held(self, held: bool):
        if held:
            self._is_shift_held = True
            opacity_effect = QGraphicsOpacityEffect(self)
            opacity_effect.setOpacity(0.3)
            if self._layout.content_layout.count() > 0:
                self._layout.content_layout.itemAt(0).widget().setGraphicsEffect(opacity_effect)
        else:
            self._is_shift_held = False
            if self._layout.content_layout.count() > 0:
                self._layout.content_layout.itemAt(0).widget().setGraphicsEffect(None)  # pyright: ignore[reportArgumentType]

    def _clear_search_query(self) -> None:
        self._layout.search_field.setText("")

    def _get_item_widget(self, index: int, library: Library) -> Any:  # pyright: ignore
        raise NotImplementedError()

    def _on_search_query_changed(self, query: str) -> None:
        self._update_items(query)

    def _on_search_query_submitted(self, query: str, always_create: bool = False) -> None:
        # Focus search field if no query
        logger.info("Query submitted")
        if not query:
            self.done.emit()
            self.hide_and_reset()
            return
        elif not self.isHidden():
            self._layout.search_field.setFocus()

        # Create and add item if no search results
        if (len(self._search_results) <= 0) or always_create:
            self._on_item_create()
        else:
            self._on_item_chosen(self._search_results[0])

        self._clear_search_query()
        self._update_items()

    def _on_item_create(self) -> None:
        raise NotImplementedError()

    def _on_item_edit(self, item: T) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def _on_item_chosen(self, item: T) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def _is_excluded(self, item: T) -> bool:
        return _item_id(item) in self.excluded

    def _update_items(self, query: str | None = None) -> None:
        """Update the item list given a search query."""
        logger.info("[SearchPanel] Updating items", limit=self._limit)

        # Get results for the search query
        query_lower = "" if not query else query.lower()
        search_results: tuple[list[T], list[T]] = self._search_items(query_lower)

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

        if self._limit > 0:
            all_results = all_results[: self._limit]

        self._search_results = all_results
        logger.info("[SearchPanel] Search results", results=self._search_results)

        for i in range(0, self._limit):
            item: T | None = all_results[i] if i < len(all_results) else None
            self._set_item_widget(item=item, index=i)

        if self._layout.content_layout.isEmpty():
            self._layout.scroll_area.setHidden(True)
            self._layout.content_layout.setContentsMargins(0, 0, 0, 0)
            self._layout.search_field.setStyleSheet(autofill_line_edit_style())
        else:
            self._layout.scroll_area.setHidden(False)
            self._layout.content_layout.setContentsMargins(6, 6, 6, 6)
            self._layout.search_field.setStyleSheet(autofill_line_edit_top_style())

    def _search_items(self, query: str) -> tuple[list[T], list[T]]:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def _set_item_widget(self, item: T | None, index: int) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def _editing_finished_callback(self):
        if self._layout.search_field.text() == "":
            self.done.emit()
            self.hide_and_reset()

    def _create_item_from_modal(self, edit_item_panel: PanelWidget) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def _edit_item(self, edit_item_panel: PanelWidget) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    @override
    def showEvent(self, event: QShowEvent) -> None:
        self._update_items()
        self._on_shift_held(held=False)
        self._layout.search_field.setDisabled(False)
        self._clear_search_query()
        return super().showEvent(event)

    @override
    def layout(self) -> SuggestBoxView:
        return self._layout

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        # When Escape is pressed, focus back on the search box.
        if event.key() in {
            QtCore.Qt.Key.Key_Escape,
            QtCore.Qt.Key.Key_Enter,
            QtCore.Qt.Key.Key_Return,
        }:
            self.hide_and_reset()
