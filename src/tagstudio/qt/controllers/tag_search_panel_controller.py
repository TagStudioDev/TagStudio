# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import TYPE_CHECKING
from warnings import catch_warnings

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QMessageBox

from tagstudio.core.constants import RESERVED_TAG_END, RESERVED_TAG_START
from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelModal
from tagstudio.qt.views.tag_search_panel_view import TagSearchPanelView

logger = structlog.get_logger(__name__)

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.mixed.build_tag import BuildTagPanel
    from tagstudio.qt.ts_qt import QtDriver


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


class TagSearchPanel(TagSearchPanelView):
    tag_chosen = Signal(int)

    _limit_items: list[tuple[str, int]] = [
        ("25", 25),
        ("50", 50),
        ("100", 100),
        ("250", 250),
        ("500", 500),
        (Translations["tag.all_tags"], -1),
    ]
    _default_limit_index: int = 0  # 25 Tag Limit (Default)

    def __init__(
        self, library: Library, exclude: list[int] | None = None, is_tag_chooser: bool = True
    ):
        super().__init__(is_tag_chooser)
        self.__lib = library
        self.__driver: QtDriver | None = None
        self.exclude: list[int] = exclude or []

        # Limits
        self.previous_limit_index: int = self._default_limit_index

        self.set_limit_items(self._limit_items)
        self.set_limit_index(self._default_limit_index)

        # Tags
        self.tags: list[Tag] = []

    def set_driver(self, driver: "QtDriver") -> None:
        self.__driver = driver

    def _on_limit_changed(self, index: int):
        logger.info("[TagSearchPanel] Updating tag limit")

        # Method was called outside the limit_combobox callback
        if index != self.get_limit_index():
            self.set_limit_index(index)

        if self.previous_limit_index == index:
            return

        self.search_tags(self.search_field.text())

    def __get_limit(self) -> tuple[str, int]:
        return self._limit_items[self.get_limit_index()]

    def __get_previous_limit(self) -> tuple[str, int]:
        return self._limit_items[self.previous_limit_index]

    def _on_search_query_changed(self, query: str) -> None:
        self.create_and_add_button.setText(Translations.format("tag.create_add", query=query))
        self.search_tags(query)

    def _on_search_query_submitted(self, query: str):
        # Focus search field if no query
        if not query:
            self.search_field.setFocus()
            self.parentWidget().hide()
            return

        # Create and add tag if no search results
        if self.tags[0] is None:
            self._on_tag_create_and_add()

        if self.is_tag_chooser:
            self.choose_tag(self.tags[0].id)

        self.clear_search_query()
        self.search_tags()

    def _on_tag_create(self) -> None:
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

        build_tag_modal.saved.connect(lambda: self.create_tag(build_tag_modal))
        build_tag_modal.show()

    def on_tag_edit(self, tag: Tag) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        edit_tag_panel: BuildTagPanel = BuildTagPanel(self.__lib, tag=tag)
        edit_tag_modal: PanelModal = PanelModal(
            edit_tag_panel,
            self.__lib.tag_display_name(tag),
            Translations["tag.edit"],
            has_save=True,
        )

        edit_tag_modal.saved.connect(lambda: self.edit_tag(edit_tag_panel))
        edit_tag_modal.show()

    def _on_tag_remove(self, tag: Tag) -> None:
        if self.is_tag_chooser:
            return

        if tag.id in range(RESERVED_TAG_START, RESERVED_TAG_END):
            return

        message_box = QMessageBox(
            QMessageBox.Question,  # type: ignore
            Translations["tag.remove"],
            Translations.format("tag.confirm_delete", tag_name=self.__lib.tag_display_name(tag)),
            QMessageBox.Ok | QMessageBox.Cancel,  # type: ignore
        )

        result = message_box.exec()

        if result != QMessageBox.Ok:  # type: ignore
            return

        self.__lib.remove_tag(tag.id)
        self.search_tags()

    def _on_tag_create_and_add(self) -> None:
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

        build_tag_modal.saved.connect(lambda: self.create_tag(build_tag_modal, choose_tag=True))
        build_tag_modal.show()

    def search_tags(self, query: str | None = None):
        """Update the tag list given a search query."""
        logger.info("[TagSearchPanel] Updating Tags", limit=self.__get_limit()[1])

        # Remove the "Create & Add" button if one exists
        self.remove_create_and_add_button()

        # Get results for the search query
        query_lower = "" if not query else query.lower()
        tag_results: list[set[Tag]] = self.__lib.search_tags(
            name=query, limit=self.__get_limit()[1]
        )

        if self.exclude:
            tag_results[0] = {tag for tag in tag_results[0] if tag.id not in self.exclude}
            tag_results[1] = {tag for tag in tag_results[1] if tag.id not in self.exclude}

        # Sort and prioritize the results
        direct_results = list(tag_results[0])
        direct_results.sort(key=lambda tag: tag.name.lower())

        ancestor_results = list(tag_results[1])
        ancestor_results.sort(key=lambda tag: tag.name.lower())

        raw_results = list(direct_results + ancestor_results)
        priority_results: set[Tag] = set()

        if query and query.strip():
            for tag in raw_results:
                if tag.name.lower().startswith(query_lower):
                    priority_results.add(tag)

        all_results: list[Tag] = sorted(list(priority_results), key=lambda tag: len(tag.name)) + [
            tag for tag in raw_results if tag not in priority_results
        ]
        if self.__get_limit()[1] > 0:
            all_results = all_results[: self.__get_limit()[1]]

        self.tags = all_results

        # Update every tag widget with the new search result data
        previous_limit: int = (
            self.__get_previous_limit()[1] > 0 and self.__get_previous_limit()[1]
        ) or len(self.__lib.tags)

        current_limit: int = (self.__get_limit()[1] > 0 and self.__get_limit()[1]) or len(
            self.__lib.tags
        )

        for i in range(0, max(previous_limit, current_limit)):
            widget_tag: Tag | None = all_results[i] if i < len(all_results) else None
            self.set_tag_widget(tag=widget_tag, index=i)

        self.previous_limit_index = self.get_limit_index()

        # Add back the "Create & Add" button
        if query and query.strip():
            self.add_create_and_add_button()

    def set_tag_widget(self, tag: Tag | None, index: int) -> None:
        """Set the tag of a tag widget at a specific index."""
        tag_widget: TagWidget = self.get_tag_widget(index, self.__lib)
        tag_widget.set_tag(tag)
        tag_widget.setHidden(tag is None)

        if tag is None:
            return
        assert tag is not None

        tag_widget.has_remove = not self.is_tag_chooser and tag.id not in range(
            RESERVED_TAG_START, RESERVED_TAG_END
        )

        # Disconnect previous callbacks
        with catch_warnings(record=True):
            tag_widget.on_edit.disconnect()
            tag_widget.on_remove.disconnect()
            tag_widget.bg_button.clicked.disconnect()
            tag_widget.search_for_tag_action.triggered.disconnect()

        # Connect callbacks
        tag_widget.on_edit.connect(lambda edit_tag=tag: self.on_tag_edit(edit_tag))
        tag_widget.on_remove.connect(lambda remove_tag=tag: self._on_tag_remove(remove_tag))
        tag_widget.bg_button.clicked.connect(lambda tag_id=tag.id: self.tag_chosen.emit(tag_id))

        # Connect search action
        if self.__driver is not None:
            tag_widget.search_for_tag_action.triggered.connect(
                lambda tag_id=tag.id: self.search_for_tag(tag_id)
            )
            tag_widget.search_for_tag_action.setEnabled(True)
        else:
            tag_widget.search_for_tag_action.setEnabled(False)

    def showEvent(self, event: QShowEvent) -> None:  # noqa N802
        self.search_tags()
        self.scroll_to(0)
        self.clear_search_query()
        return super().showEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        # When Escape is pressed, focus back on the search box.
        # If focus is already on the search box, close the modal.
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.search_field.hasFocus():
                super().keyPressEvent(event)
            else:
                self.focus_search_box(select_all=True)

    def choose_tag(self, tag_id: int) -> None:
        self.tag_chosen.emit(tag_id)

    def create_tag(self, build_tag_modal: PanelModal, choose_tag: bool = False) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        if isinstance(build_tag_modal.widget, BuildTagPanel):
            tag: Tag = build_tag_modal.widget.build_tag()
            self.__lib.add_tag(
                tag,
                parent_ids=build_tag_modal.widget.parent_ids,
                alias_names=build_tag_modal.widget.alias_names,
                alias_ids=build_tag_modal.widget.alias_ids,
            )

            if choose_tag:
                self.choose_tag(tag.id)
                self.clear_search_query()

        build_tag_modal.hide()
        self._on_search_query_changed(self.get_search_query())

    def edit_tag(self, edit_tag_panel: "BuildTagPanel") -> None:
        self.__lib.update_tag(
            tag=edit_tag_panel.build_tag(),
            parent_ids=edit_tag_panel.parent_ids,
            alias_names=edit_tag_panel.alias_names,
            alias_ids=edit_tag_panel.alias_ids,
        )

        self.search_tags(self.search_field.text())

    def search_for_tag(self, tag_id: int) -> None:
        if self.__driver is None:
            return

        self.__driver.main_window.search_field.setText(f"tag_id:{tag_id}")
        self.__driver.update_browsing_state(
            BrowsingState.from_tag_id(tag_id, self.__driver.browsing_history.current)
        )
