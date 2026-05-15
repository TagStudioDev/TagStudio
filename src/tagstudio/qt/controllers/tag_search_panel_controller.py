# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import TYPE_CHECKING
from warnings import catch_warnings

import structlog
from PySide6.QtWidgets import QMessageBox

from tagstudio.core.constants import RESERVED_TAG_END, RESERVED_TAG_START
from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.controllers.search_panel_controller import SearchPanel
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelModal, PanelWidget
from tagstudio.qt.views.tag_search_panel_view import TagSearchPanelView

logger = structlog.get_logger(__name__)

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    pass


class TagSearchModal(PanelModal):
    tsp: "TagSearchPanel"

    def __init__(
        self,
        library: Library,
        exclude: list[int] | None = None,
        is_tag_chooser: bool = True,
        done_callback=None,
        save_callback=None,
        has_save=False,
    ):
        self.tsp = TagSearchPanel(library, exclude, is_tag_chooser)
        super().__init__(
            self.tsp,
            Translations["tag.add.plural"],
            done_callback=done_callback,
            save_callback=save_callback,
            has_save=has_save,
        )


class TagSearchPanel(SearchPanel[Tag], TagSearchPanelView):
    def __init__(
        self, library: Library, exclude: list[int] | None = None, is_tag_chooser: bool = True
    ):
        super().__init__(exclude, is_tag_chooser)
        self.__lib = library

        self._unlimited_limit_item_label = Translations["tag.all_tags"]
        self._create_and_add_button_label_key = "tag.create_add"

    def _get_max_limit(self) -> int:
        return len(self.__lib.tags)

    def _on_item_create(self) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        query: str = self.get_search_query()

        build_tag_panel: BuildTagPanel = BuildTagPanel(self.__lib)
        build_tag_modal: PanelModal = PanelModal(
            build_tag_panel,
            Translations["tag.new"],
            has_save=True,
        )

        if query.strip():
            build_tag_panel.name_field.setText(query)

        build_tag_modal.saved.connect(lambda: self.create_item(build_tag_modal))
        build_tag_modal.show()

    def on_item_edit(self, item: Tag) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        edit_tag_panel: BuildTagPanel = BuildTagPanel(self.__lib, tag=item)
        edit_tag_modal: PanelModal = PanelModal(
            edit_tag_panel,
            self.__lib.tag_display_name(item),
            Translations["tag.edit"],
            has_save=True,
        )

        edit_tag_modal.saved.connect(lambda: self.edit_item(edit_tag_panel))
        edit_tag_modal.show()

    def _on_item_remove(self, item: Tag) -> None:
        if self.is_chooser:
            return

        if item.id in range(RESERVED_TAG_START, RESERVED_TAG_END):
            return

        message_box = QMessageBox(
            QMessageBox.Question,  # type: ignore
            Translations["tag.remove"],
            Translations.format("tag.confirm_delete", tag_name=self.__lib.tag_display_name(item)),
            QMessageBox.Ok | QMessageBox.Cancel,  # type: ignore
        )

        result = message_box.exec()

        if result != QMessageBox.Ok:  # type: ignore
            return

        self.__lib.remove_tag(item.id)
        self.update_items(self.get_search_query())

    def _on_item_create_and_add(self) -> None:
        """Opens "Create Tag" panel to create and add a new tag with given name."""
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        query: str = self.get_search_query()

        logger.info("Create and Add Tag", name=query)

        build_tag_panel: BuildTagPanel = BuildTagPanel(self.__lib)
        build_tag_modal: PanelModal = PanelModal(
            build_tag_panel,
            Translations["tag.new"],
            Translations["tag.add"],
            has_save=True,
        )

        if query.strip():
            build_tag_panel.name_field.setText(query)

        build_tag_modal.saved.connect(lambda: self.create_item(build_tag_modal, choose_item=True))
        build_tag_modal.show()

    def _on_item_chosen(self, item: Tag) -> None:
        self.item_chosen.emit(item.id)

    def search_items(self, query: str) -> tuple[list[Tag], list[Tag]]:
        return self.__lib.search_tags(name=query, limit=self._get_limit()[1])

    def set_item_widget(self, item: Tag | None, index: int) -> None:
        """Set the tag of a tag widget at a specific index."""
        tag_widget: TagWidget = self.get_item_widget(index, self.__lib)
        tag_widget.set_tag(item)
        tag_widget.setHidden(item is None)

        if item is None:
            return
        assert item is not None

        tag_widget.has_remove = not self.is_chooser and item.id not in range(
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
        tag_widget.bg_button.clicked.connect(
            lambda checked=False, tag=item: self._on_item_chosen(tag)
        )

        # Connect search action
        if self._driver is not None:
            tag_widget.search_for_tag_action.triggered.connect(
                lambda tag_id=item.id: self.search_for_tag(tag_id)
            )
            tag_widget.search_for_tag_action.setEnabled(True)
        else:
            tag_widget.search_for_tag_action.setEnabled(False)

    def create_item(self, build_item_modal: PanelModal, choose_item: bool = False) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        if isinstance(build_item_modal.widget, BuildTagPanel):
            tag: Tag = build_item_modal.widget.build_tag()
            self.__lib.add_tag(
                tag,
                parent_ids=build_item_modal.widget.parent_ids,
                alias_names=build_item_modal.widget.alias_names,
                alias_ids=build_item_modal.widget.alias_ids,
            )

            if choose_item:
                self._on_item_chosen(tag)
                self.clear_search_query()

        build_item_modal.hide()
        self._on_search_query_changed(self.get_search_query())

    def edit_item(self, edit_item_panel: PanelWidget) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        if not isinstance(edit_item_panel, BuildTagPanel):
            return
        self.__lib.update_tag(
            tag=edit_item_panel.build_tag(),
            parent_ids=edit_item_panel.parent_ids,
            alias_names=edit_item_panel.alias_names,
            alias_ids=edit_item_panel.alias_ids,
        )

        self.update_items(self.search_field.text())

    def search_for_tag(self, tag_id: int) -> None:
        if self._driver is None:
            return

        self._driver.main_window.search_field.setText(f"tag_id:{tag_id}")
        self._driver.update_browsing_state(
            BrowsingState.from_tag_id(tag_id, self._driver.browsing_history.current)
        )
