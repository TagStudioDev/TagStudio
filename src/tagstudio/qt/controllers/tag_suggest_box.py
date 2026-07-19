# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from typing import override
from warnings import catch_warnings

import structlog
from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.controllers.suggest_box import SuggestBox
from tagstudio.qt.controllers.underlined_widget import UnderlinedWidget
from tagstudio.qt.mixed.build_tag import BuildTagPanel
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelModal, PanelWidget
from tagstudio.qt.views.suggest_box_view import SuggestBoxView

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class TagSuggestBox(SuggestBox[Tag]):
    def __init__(self, driver: "QtDriver", view: SuggestBoxView | None = None):
        super().__init__(driver, view=view or SuggestBoxView())
        self._driver = driver
        self._lib = self._driver.lib

        # Context Menu Actions
        edit_tag_on_create_action = QAction(Translations["settings.edit_tag_on_create"], self)
        edit_tag_on_create_action.setCheckable(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.addAction(edit_tag_on_create_action)
        self.layout().search_field.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.layout().search_field.addAction(edit_tag_on_create_action)
        edit_tag_on_create_action.setChecked(self._driver.settings.edit_tag_on_create)
        edit_tag_on_create_action.triggered.connect(
            lambda checked: self.toggle_edit_on_tag_create(checked)
        )

    def _search_for_tag_callback(self, tag_id: int) -> None:
        self._driver.main_window.search_field.setText(f"tag_id:{tag_id}")
        self._driver.update_browsing_state(
            BrowsingState.from_tag_id(tag_id, self._driver.browsing_history.current)
        )

    def toggle_edit_on_tag_create(self, checked: bool) -> None:
        """Toggle the setting for opening the edit window after creating a tag."""
        self._driver.settings.edit_tag_on_create = checked
        self._driver.settings.save()

    @override
    def _on_item_create(self) -> None:
        """Opens panel to create a new tag and optionally add it to an entry.

        Populates name field using current search query.

        Args:
            add_to_entry (bool): Should this item be added to currently selected entries?
        """
        query: str = self.layout().search_field.text()

        if self._driver.settings.edit_tag_on_create:
            panel: BuildTagPanel = BuildTagPanel(self._lib)
            modal: PanelModal = PanelModal(
                panel, Translations["tag.new"], Translations["tag.new"], is_savable=True
            )
            if query.strip():
                panel.name_field.setText(query)

            modal.saved.connect(lambda: self._create_item_from_modal(panel))
            modal.show()
        else:
            tag = Tag(name=query)
            self._lib.add_tag(tag)
            self._on_item_chosen(tag)
            self._clear_search_query()

    @override
    def _on_item_edit(self, item: Tag) -> None:
        edit_tag_panel: BuildTagPanel = BuildTagPanel(self._lib, tag=item)
        edit_tag_modal: PanelModal = PanelModal(
            edit_tag_panel,
            self._lib.tag_display_name(item),
            Translations["tag.edit"],
            is_savable=True,
        )
        edit_tag_modal.saved.connect(lambda: self._edit_item(edit_tag_panel))
        edit_tag_modal.show()

    @override
    def _on_item_chosen(self, item: Tag) -> None:
        self.item_chosen.emit(item.id)
        self.done.emit()

    @override
    def _search_items(self, query: str) -> tuple[list[Tag], list[Tag]]:
        if query != "":
            return self._lib.search_tags(name=query, limit=0)
        else:
            return ([], [])

    @override
    def _set_item_widget(self, item: Tag | None, index: int) -> None:
        """Set the tag of a tag widget at a specific index."""
        underlined_widget: UnderlinedWidget = self._get_item_widget(index, self._lib)
        tag_widget = underlined_widget.widget
        assert isinstance(tag_widget, TagWidget)
        tag_widget.has_remove = False
        tag_widget.set_tag(item)
        underlined_widget.setHidden(item is None)
        opacity_effect = QGraphicsOpacityEffect(self)
        opacity_effect.setOpacity(0.3)
        if item and item.id in self.added:
            tag_widget.setGraphicsEffect(opacity_effect)
        else:
            tag_widget.setGraphicsEffect(None)  # pyright: ignore[reportArgumentType]

        if item is None:
            return

        # TODO: Add tabbing to different items, and use underline to indicate which will be added
        underlined_widget.toggle_underline(index != 0)

        # Disconnect previous callbacks
        with catch_warnings(record=True):
            tag_widget.on_edit.disconnect()
            tag_widget.bg_button.clicked.disconnect()
            tag_widget.search_for_tag_action.triggered.disconnect()

        # Connect callbacks
        tag_widget.on_edit.connect(lambda edit_tag=item: self._on_item_edit(edit_tag))
        tag_widget.bg_button.clicked.connect(
            lambda checked=False, tag=item: self._on_item_chosen(tag)
        )
        tag_widget.search_for_tag_action.triggered.connect(
            lambda checked=False, tag_id=item.id: self._search_for_tag_callback(tag_id)
        )
        tag_widget.search_for_tag_action.setEnabled(True)

    @override
    def _create_item_from_modal(self, edit_item_panel: PanelWidget) -> None:
        if isinstance(edit_item_panel, BuildTagPanel):
            tag: Tag = edit_item_panel.build_tag()
            self._lib.add_tag(
                tag, parent_ids=edit_item_panel.parent_ids, aliases=edit_item_panel.aliases
            )
            self._on_item_chosen(tag)
            self._clear_search_query()

        edit_item_panel.hide()
        self._on_search_query_changed(self.layout().search_field.text())

    @override
    def _edit_item(self, edit_item_panel: PanelWidget) -> None:
        if not isinstance(edit_item_panel, BuildTagPanel):
            return

        self._lib.update_tag(
            tag=edit_item_panel.build_tag(),
            parent_ids=edit_item_panel.parent_ids,
            aliases=edit_item_panel.aliases,
        )
        self._update_items(self.layout().search_field.text())

    @override
    def _get_item_widget(self, index: int, library: Library | None) -> UnderlinedWidget:
        """Gets the item widget at a specific index."""
        # Create any new item widgets needed up to the given index
        if self.layout().content_layout.count() <= index:
            while self.layout().content_layout.count() <= index:
                tag_widget = TagWidget(tag=None, has_edit=True, has_remove=True, library=library)
                tag_widget.on_remove.connect(self._update_items)
                widget = UnderlinedWidget(tag_widget)
                widget.setHidden(True)
                self.layout().content_layout.addWidget(widget)

        widget_: QWidget = self.layout().content_layout.itemAt(index).widget()
        assert isinstance(widget_, UnderlinedWidget)
        return widget_
