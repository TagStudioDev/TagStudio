# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override
from warnings import catch_warnings

import structlog
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox, QWidget
from typing_extensions import deprecated

from tagstudio.core.constants import RESERVED_TAG_END, RESERVED_TAG_START
from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.controllers.search_panel_controller import SearchPanel
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.search_panel_view import SearchPanelView

logger = structlog.get_logger(__name__)


class TagSearchPanel(SearchPanel[Tag]):
    search_for_tag = Signal(int)

    def __init__(
        self,
        library: Library,
        exclude: list[int] | None = None,
        is_chooser: bool = True,
        view: SearchPanelView | None = None,
    ):
        super().__init__(
            view=view or SearchPanelView(Translations["home.search_tags"], is_chooser=is_chooser),
            exclude=exclude,
            is_chooser=is_chooser,
        )
        self._lib = library
        self._unlimited_limit_item_label = Translations["tag.all_tags"]
        self._create_and_add_button_key = "tag.create_add"

    @override
    def _get_max_limit(self) -> int:
        return len(self._lib.tags)

    @override
    def on_item_create(self, add_to_entry: bool = False) -> None:
        """Opens panel to create a new tag and optionally add it to an entry.

        Populates name field using current search query.

        Args:
            add_to_entry (bool): Should this item be added to currently selected entries?
        """
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        query: str = self.get_search_query()
        panel: BuildTagPanel = BuildTagPanel(self._lib)
        modal: Modal = Modal(
            panel,
            Translations["tag.new"],
            Translations["tag.add"] if add_to_entry else Translations["tag.new"],
            is_savable=True,
        )

        if query.strip():
            panel.name_field.setText(query)

        modal.saved.connect(lambda: self.create_item(panel, choose_item=add_to_entry))
        modal.show()

    @override
    def on_item_edit(self, item: Tag) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        edit_tag_panel: BuildTagPanel = BuildTagPanel(self._lib, tag=item)
        edit_tag_modal: Modal = Modal(
            edit_tag_panel,
            self._lib.tag_display_name(item),
            Translations["tag.edit"],
            is_savable=True,
        )
        edit_tag_modal.saved.connect(lambda: self.edit_item(edit_tag_panel))
        edit_tag_modal.show()

    @override
    def _on_item_remove(self, item: Tag) -> None:
        if self._is_chooser:
            return

        if item.id in range(RESERVED_TAG_START, RESERVED_TAG_END):
            return

        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            Translations["tag.remove"],
            Translations.format("tag.confirm_delete", tag_name=self._lib.tag_display_name(item)),
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )

        result = message_box.exec()

        if result != QMessageBox.StandardButton.Ok:
            return

        self._lib.remove_tag(item.id)
        self.update_items(self.get_search_query())

    @override
    def _on_item_chosen(self, item: Tag) -> None:
        self.item_chosen.emit(item.id)

    @override
    def search_items(self, query: str) -> tuple[list[Tag], list[Tag]]:
        return self._lib.search_tags(name=query, limit=self._get_limit()[1])

    @override
    def set_item_widget(self, item: Tag | None, index: int) -> None:
        """Set the tag of a tag widget at a specific index."""
        tag_widget: TagWidget = self.get_item_widget(index, self._lib)
        tag_widget.set_tag(item)
        tag_widget.setHidden(item is None)

        if item is None:
            return
        assert item is not None

        tag_widget.has_remove = not self._is_chooser and item.id not in range(
            RESERVED_TAG_START, RESERVED_TAG_END
        )

        # Disconnect previous callbacks
        with catch_warnings(record=True):
            tag_widget.on_edit.disconnect()
            tag_widget.on_remove.disconnect()
            tag_widget.bg_button.clicked.disconnect()
            tag_widget.search_for_tag_action.triggered.disconnect()

        # Connect callbacks
        tag_widget.on_edit.connect(lambda edit_tag=item: self.on_item_edit(edit_tag))
        tag_widget.on_remove.connect(lambda remove_tag=item: self._on_item_remove(remove_tag))
        if self._is_chooser:
            tag_widget.bg_button.clicked.connect(
                lambda checked=False, tag=item: self._on_item_chosen(tag)
            )
        else:
            tag_widget.bg_button.clicked.connect(
                lambda checked=False, edit_tag=item: self.on_item_edit(edit_tag)
            )

        # Connect search action
        tag_widget.search_for_tag_action.triggered.connect(
            lambda checked=False, tag_id=item.id: self.search_for_tag.emit(tag_id)
        )
        tag_widget.search_for_tag_action.setEnabled(True)

    @override
    def create_item(self, edit_item_panel: ModalContent, choose_item: bool = False) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        if isinstance(edit_item_panel, BuildTagPanel):
            tag: Tag = edit_item_panel.build_tag()
            self._lib.add_tag(
                tag, parent_ids=edit_item_panel.parent_ids, aliases=edit_item_panel.aliases
            )

            if choose_item:
                self._on_item_chosen(tag)
                self.clear_search_query()

        edit_item_panel.hide()
        self.on_search_query_changed(self.get_search_query())

    @override
    def edit_item(self, edit_item_panel: ModalContent) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        if not isinstance(edit_item_panel, BuildTagPanel):
            return

        self._lib.update_tag(
            tag=edit_item_panel.build_tag(),
            parent_ids=edit_item_panel.parent_ids,
            aliases=edit_item_panel.aliases,
        )
        self.update_items(self.layout().search_field.text())

    @deprecated("Put this callback in the driver!")
    def _search_for_tag_callback(self, tag_id: int) -> None:
        if self._driver is None:
            return

        # TODO: This should be a callback, the driver does not need to be passed for this.
        self._driver.main_window.search_field.setText(f"tag_id:{tag_id}")
        self._driver.update_browsing_state(
            BrowsingState.from_tag_id(tag_id, self._driver.browsing_history.current)
        )

    @override
    def get_item_widget(self, index: int, library: Library | None) -> TagWidget:
        """Gets the item widget at a specific index."""
        # Create any new item widgets needed up to the given index
        if self.layout().scroll_layout.count() <= index:
            while self.layout().scroll_layout.count() <= index:
                pad_tag_widget = TagWidget(
                    tag=None, has_edit=True, has_remove=True, library=library
                )
                pad_tag_widget.setHidden(True)
                self.layout().scroll_layout.addWidget(pad_tag_widget)

        tag_widget: QWidget = self.layout().scroll_layout.itemAt(index).widget()
        assert isinstance(tag_widget, TagWidget)
        return tag_widget
