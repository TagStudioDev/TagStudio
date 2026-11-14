# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import TYPE_CHECKING, Any, override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QSizePolicy

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.views.capsule_view import CapsuleView
from tagstudio.qt.views.search_panel_view import SearchPanelView
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, PAD

logger = structlog.get_logger(__name__)

_ROW_HEIGHT = CapsuleView.HEIGHT + HALF_PAD  # Each capsule and the gap below it

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


def _item_id(item: object) -> int:
    item_id: Any = getattr(item, "id")  # noqa: B009

    if isinstance(item_id, int):
        return item_id
    else:
        raise AttributeError()


def _item_name(item: object) -> str:
    item_name: Any = getattr(item, "name")  # noqa: B009

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
        self._is_create_from_query_button_in_layout = False

        # Items
        self._excluded: list[int] = exclude or []
        self._search_results: list[T] = []
        self._item_widgets: list[Capsule] = []
        self._are_capsules_clickable = True
        self._first_row = 0
        self._item_widget_rows: list[int | None] = []

        self.setLayout(view)
        scroll_bar = view.scroll_area.verticalScrollBar()
        scroll_bar.rangeChanged.connect(self._toggle_scroll_bar)
        self._toggle_scroll_bar(scroll_bar.minimum(), scroll_bar.maximum())
        scroll_bar.valueChanged.connect(self._fill_item_widgets)
        view.scroll_area.viewport().installEventFilter(self)
        self.setMinimumSize(300, 400)
        self._connect_callbacks()

    def _connect_callbacks(self) -> None:
        self.layout().search_field.textChanged.connect(self.on_search_query_changed)
        self.layout().search_field.returnPressed.connect(
            lambda: self.on_search_query_submitted(self.get_search_query())
        )
        self.layout().create_button.clicked.connect(self.on_item_create)
        self.layout().create_from_query_button.on_click.connect(self.on_item_create)

    def focus_search_box(self, select_all: bool = False) -> None:
        self.layout().search_field.setFocus()
        if select_all:
            self.layout().search_field.selectAll()

    def get_search_query(self) -> str:
        return self.layout().search_field.text()

    def set_search_query(self, query: str) -> None:
        self.layout().search_field.setText(query)

    def clear_search_query(self) -> None:
        self.layout().search_field.setText("")
        self.focus_search_box()

    # Item list
    def scroll_to(self, position: int) -> None:
        self.layout().scroll_area.verticalScrollBar().setValue(position)

    def add_create_from_query_button(self) -> None:
        if self._is_create_from_query_button_in_layout:
            return
        self.layout().scroll_layout.addWidget(self.layout().create_from_query_button)
        self.layout().create_from_query_button.restyle()
        self.layout().create_from_query_button.show()
        self._is_create_from_query_button_in_layout = True

    def remove_create_from_query_button(self) -> None:
        if not self._is_create_from_query_button_in_layout:
            return
        self.layout().scroll_layout.removeWidget(self.layout().create_from_query_button)
        self.layout().create_from_query_button.hide()
        self._is_create_from_query_button_in_layout = False

    def _toggle_scroll_bar(self, minimum: int, maximum: int) -> None:
        """Show the scroll bar when needed."""
        view = self.layout()
        is_overflowing = maximum > minimum
        margins = view.results_layout.contentsMargins()
        margins.setRight(0 if is_overflowing else PAD)
        view.results_layout.setContentsMargins(margins)
        view.results_layout.activate()
        view.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
            if is_overflowing
            else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

    def get_item_widget(self, index: int) -> Capsule:
        """The item widget showing the result at this row, which must be in view."""
        return self._item_widgets[index - self._first_row]

    def _new_item_widget(self) -> Capsule:
        raise NotImplementedError()

    def set_capsules_clickable(self, clickable: bool) -> None:
        self._are_capsules_clickable = clickable
        for capsule in self._item_widgets:
            capsule.set_clickable(clickable)

    def on_search_query_changed(self, query: str) -> None:
        self.layout().create_from_query_button.set_text(
            Translations.format("item.create_from_query", query=query)
        )
        self.update_items(query)
        self.scroll_to(0)

    def on_search_query_submitted(self, query: str) -> None:
        # Focus search field if no query
        if not query:
            self.layout().search_field.setFocus()
            window = self.window()
            if isinstance(window, Modal):
                window.hide()
            return

        # Create item if no search results
        if len(self._search_results) <= 0:
            self.on_item_create()
            return

        if not self._are_capsules_clickable:
            return

        if self._is_chooser:
            self._on_item_chosen(self._search_results[0])

        self.clear_search_query()
        self.update_items()

    def on_item_create(self) -> None:
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
        logger.info("[SearchPanel] Updating items")

        # Remove the create from query button if one exists
        self.remove_create_from_query_button()

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

        self._search_results = all_results
        logger.info("[SearchPanel] Search results", count=len(self._search_results))
        self._update_item_widgets()

        # Add back the create from query button
        if query and query.strip():
            self.add_create_from_query_button()

    def _update_item_widgets(self) -> None:
        """Show the search results in the item widgets."""
        view = self.layout()
        view.rows_spacer.changeSize(
            0, len(self._search_results) * _ROW_HEIGHT, QSizePolicy.Policy.Minimum
        )
        view.scroll_layout.invalidate()
        self._item_widget_rows = [None for _ in self._item_widgets]
        self._fill_item_widgets()

    def _fill_item_widgets(self) -> None:
        """Fill item widgets for the rows in view, reusing them as other rows scroll in."""
        view = self.layout()
        viewport = view.scroll_area.viewport()
        margins = view.scroll_layout.contentsMargins()
        scroll_position = view.scroll_area.verticalScrollBar().value()
        self._first_row = max(0, scroll_position - margins.top()) // _ROW_HEIGHT

        # Two extra rows for the partly shown rows at the top and bottom
        while len(self._item_widgets) < viewport.height() // _ROW_HEIGHT + 2:
            item_widget = self._new_item_widget()
            item_widget.setParent(view.scroll_contents)
            item_widget.set_clickable(self._are_capsules_clickable)
            self._item_widgets.append(item_widget)
            self._item_widget_rows.append(None)

        width = viewport.width() - margins.left() - margins.right()
        for slot, item_widget in enumerate(self._item_widgets):
            row = self._first_row + slot
            if row >= len(self._search_results):
                item_widget.setHidden(True)
                self._item_widget_rows[slot] = None
                continue
            top = margins.top() + row * _ROW_HEIGHT
            item_widget.setGeometry(margins.left(), top, width, CapsuleView.HEIGHT)
            # Only fill when the slot's row changes, avoiding refills on resizes
            if self._item_widget_rows[slot] != row:
                self._item_widget_rows[slot] = row
                item_widget.setHidden(False)
                self.set_item_widget(self._search_results[row], row)

    def search_items(self, query: str) -> tuple[list[T], list[T]]:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def set_item_widget(self, item: T, index: int) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    @override
    def layout(self) -> SearchPanelView:
        """Return the typed layout for this widget."""
        return super().layout()  # pyright: ignore[reportReturnType]

    @override
    def showEvent(self, event: QShowEvent) -> None:
        if isinstance(self.window(), Modal):
            self.update_items()
            self.scroll_to(0)
            self.clear_search_query()
        else:
            self.update_items(self.get_search_query())
        return super().showEvent(event)

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Resize:
            self._fill_item_widgets()
        return super().eventFilter(watched, event)

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        # When Escape is pressed, focus back on the search box.
        # If focus is already on the search box, close the modal.
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.layout().search_field.hasFocus():
                super().keyPressEvent(event)
            else:
                self.focus_search_box(select_all=True)

    def create_item(self, edit_item_panel: ModalContent) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def edit_item(self, edit_item_panel: ModalContent) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()
