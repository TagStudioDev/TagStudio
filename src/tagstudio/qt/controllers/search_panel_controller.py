# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import TYPE_CHECKING, Any, override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.search_panel_view import SearchPanelView

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


class SearchPanel[T](ModalContent):
    item_chosen = Signal(int)

    def __init__(
        self,
        view: SearchPanelView,
        exclude: list[int] | None = None,
        is_chooser: bool = True,
    ) -> None:
        super().__init__()
        self._driver: QtDriver | None = None
        self._is_chooser = is_chooser
        self._create_and_add_button_in_layout = False
        self._create_and_add_button_key: str = ""

        # Items
        self._excluded: list[int] = exclude or []
        self._search_results: list[T] = []

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
        self._default_limit_index: int = 0  # 25 Limit (Default)
        self._previous_limit_index: int = self._default_limit_index

        self.setLayout(view)
        self.set_limit_items(self._limit_items)
        self.set_limit_index(self._default_limit_index)
        self.setMinimumSize(300, 400)
        self.connect_callbacks(self)

    def connect_callbacks(self, controller: "SearchPanel[Any]") -> None:  # pyright: ignore[reportExplicitAny]
        self.layout().limit_combobox.currentIndexChanged.connect(controller.on_limit_changed)
        self.layout().search_field.textChanged.connect(controller.on_search_query_changed)
        self.layout().search_field.returnPressed.connect(
            lambda: controller.on_search_query_submitted(self.get_search_query())
        )
        self.layout().create_button.clicked.connect(controller.on_item_create)
        self.layout().create_and_add_button.clicked.connect(
            lambda: controller.on_item_create(add_to_entry=True)
        )

    def set_limit_items(self, limit_items: list[tuple[str, int]]) -> None:
        # Remove existing limit items
        for i in reversed(range(self.layout().limit_combobox.count())):
            self.layout().limit_combobox.removeItem(i)

        # Add new limit items
        self.layout().limit_combobox.addItems([limit_item[0] for limit_item in limit_items])

    def get_limit_index(self) -> int:
        return self.layout().limit_combobox.currentIndex()

    def set_limit_index(self, index: int) -> None:
        self.layout().limit_combobox.setCurrentIndex(index)

    def focus_search_box(self, select_all: bool = False) -> None:
        self.layout().search_field.setFocus()
        if select_all:
            self.layout().search_field.selectAll()

    def get_search_query(self) -> str:
        return self.layout().search_field.text()

    def clear_search_query(self) -> None:
        self.layout().search_field.setText("")
        self.focus_search_box()

    # Item list
    def scroll_to(self, position: int) -> None:
        self.layout().scroll_area.verticalScrollBar().setValue(position)

    def add_create_and_add_button(self) -> None:
        if self._create_and_add_button_in_layout:
            return
        self.layout().scroll_layout.addWidget(self.layout().create_and_add_button)
        self.layout().create_and_add_button.show()
        self._create_and_add_button_in_layout = True

    def remove_create_and_add_button(self) -> None:
        if not self._create_and_add_button_in_layout:
            return
        self.layout().scroll_layout.removeWidget(self.layout().create_and_add_button)
        self.layout().create_and_add_button.hide()
        self._create_and_add_button_in_layout = False

    def get_item_widget(self, index: int, library: Library) -> Any:  # pyright: ignore[reportExplicitAny]
        return self.get_item_widget(index, library)

    def on_limit_changed(self, index: int) -> None:
        # Method was called outside the limit_combobox callback
        if index != self.get_limit_index():
            self.set_limit_index(index)

        if self._previous_limit_index == index:
            return

        self.update_items(self.layout().search_field.text())

    def _get_limit(self) -> tuple[str, int]:
        return self._limit_items[self.get_limit_index()]

    def _get_previous_limit(self) -> tuple[str, int]:
        return self._limit_items[self._previous_limit_index]

    def _get_max_limit(self) -> int:
        raise NotImplementedError()

    def on_search_query_changed(self, query: str) -> None:
        self.layout().create_and_add_button.setText(
            Translations.format(self._create_and_add_button_key, query=query)
        )
        self.update_items(query)

    def on_search_query_submitted(self, query: str) -> None:
        # Focus search field if no query
        if not query:
            self.layout().search_field.setFocus()
            parent: QWidget | None = self.parentWidget()
            if parent is not None:  # pyright: ignore[reportUnnecessaryComparison]
                parent.hide()
            return

        # Create and add item if no search results
        if len(self._search_results) <= 0:
            self.on_item_create(add_to_entry=True)
        elif self._is_chooser:
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
        return _item_id(item) in self._excluded

    def update_items(self, query: str | None = None) -> None:
        """Update the item list given a search query."""
        logger.info("[SearchPanel] Updating items", limit=self._get_limit()[1])

        # Remove the "Create & Add" button if one exists
        self.remove_create_and_add_button()

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
        if self._get_limit()[1] > 0:
            all_results = all_results[: self._get_limit()[1]]

        self._search_results = all_results
        logger.info("[SearchPanel] Search results", results=self._search_results)

        # Update every item widget with the new search result data
        previous_limit: int = (
            self._get_previous_limit()[1] > 0 and self._get_previous_limit()[1]
        ) or self._get_max_limit()
        current_limit: int = (
            self._get_limit()[1] > 0 and self._get_limit()[1]
        ) or self._get_max_limit()

        for i in range(0, max(previous_limit, current_limit)):
            item: T | None = all_results[i] if i < len(all_results) else None
            self.set_item_widget(item=item, index=i)

        self._previous_limit_index = self.get_limit_index()

        # Add back the "Create & Add" button
        if query and query.strip():
            self.add_create_and_add_button()

    def search_items(self, query: str) -> tuple[list[T], list[T]]:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def set_item_widget(self, item: T | None, index: int) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    @override
    def layout(self) -> SearchPanelView:
        """Return the typed layout for this widget."""
        return super().layout()  # pyright: ignore[reportReturnType]

    @override
    def showEvent(self, event: QShowEvent) -> None:  # noqa N802
        self.update_items()
        self.scroll_to(0)
        self.clear_search_query()
        return super().showEvent(event)

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        # When Escape is pressed, focus back on the search box.
        # If focus is already on the search box, close the modal.
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.layout().search_field.hasFocus():
                super().keyPressEvent(event)
            else:
                self.focus_search_box(select_all=True)

    def create_item(self, edit_item_panel: ModalContent, choose_item: bool = False) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def edit_item(self, edit_item_panel: ModalContent) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()
