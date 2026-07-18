# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override
from warnings import catch_warnings

import structlog
from PySide6.QtWidgets import QGraphicsOpacityEffect, QMessageBox, QSizePolicy, QWidget

from tagstudio.core.constants import RESERVED_TAG_END, RESERVED_TAG_START
from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.controllers.suggest_box_controller import SuggestBox
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelModal, PanelWidget
from tagstudio.qt.views.tag_suggest_box_view import TagSuggestBoxView

logger = structlog.get_logger(__name__)


class TagSuggestBox(SuggestBox[Tag]):
    def __init__(
        self,
        library: Library,
        exclude: list[int] | None = None,
        is_tag_chooser: bool = True,
        view: TagSuggestBoxView | None = None,
    ):
        super().__init__(
            view=view or TagSuggestBoxView(is_tag_chooser),
            exclude=exclude,
            is_chooser=is_tag_chooser,
        )
        self.__lib = library

        self._unlimited_limit_item_label = Translations["tag.all_tags"]
        self._create_and_add_button_label_key = "tag.create_add"

    @override
    def _get_max_limit(self) -> int:
        return len(self.__lib.tags)

    @override
    def on_item_create(self, add_to_entry: bool = False) -> None:
        """Opens panel to create a new tag and optionally add it to an entry.

        Populates name field using current search query.

        Args:
            add_to_entry (bool): Should this item be added to currently selected entries?
        """
        # TODO: Move this to a top-level import

        query: str = self.view.search_field.text()

        # panel: BuildTagPanel = BuildTagPanel(self.__lib)
        # modal: PanelModal = PanelModal(
        #     panel,
        #     Translations["tag.new"],
        #     Translations["tag.add"] if add_to_entry else Translations["tag.new"],
        #     is_savable=True,
        # )

        # if query.strip():
        #     panel.name_field.setText(query)

        # modal.saved.connect(lambda: self.create_item(panel, choose_item=add_to_entry))
        # modal.show()
        tag = Tag(name=query)
        self.__lib.add_tag(tag)
        if add_to_entry:
            self._on_item_chosen(tag)
            self.clear_search_query()

    @override
    def on_item_edit(self, item: Tag) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        edit_tag_panel: BuildTagPanel = BuildTagPanel(self.__lib, tag=item)
        edit_tag_modal: PanelModal = PanelModal(
            edit_tag_panel,
            self.__lib.tag_display_name(item),
            Translations["tag.edit"],
            is_savable=True,
        )
        edit_tag_modal.saved.connect(lambda: self.edit_item(edit_tag_panel))
        edit_tag_modal.show()

    @override
    def _on_item_remove(self, item: Tag) -> None:
        if self.is_chooser:
            return

        if item.id in range(RESERVED_TAG_START, RESERVED_TAG_END):
            return

        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            Translations["tag.remove"],
            Translations.format("tag.confirm_delete", tag_name=self.__lib.tag_display_name(item)),
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )

        result = message_box.exec()

        if result != QMessageBox.StandardButton.Ok:
            return

        self.__lib.remove_tag(item.id)
        self.update_items(self.view.search_field.text())

    @override
    def _on_item_chosen(self, item: Tag) -> None:
        self.item_chosen.emit(item.id)
        self.done.emit()

    @override
    def search_items(self, query: str) -> tuple[list[Tag], list[Tag]]:
        if query != "":
            # return self.__lib.search_tags(name=query, limit=self._get_limit()[1])
            return self.__lib.search_tags(name=query, limit=0)
        else:
            return ([], [])

    @override
    def set_item_widget(self, item: Tag | None, index: int) -> None:
        """Set the tag of a tag widget at a specific index."""
        tag_widget: TagWidget = self.get_item_widget(index, self.__lib)
        tag_widget.set_tag(item)
        tag_widget.setHidden(item is None)
        if item and item.id in self.added:
            opacity_effect = QGraphicsOpacityEffect(self)
            opacity_effect.setOpacity(0.3)
            tag_widget.setGraphicsEffect(opacity_effect)
        else:
            tag_widget.setGraphicsEffect(None)  # pyright: ignore[reportArgumentType]

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
        if self.is_chooser:
            tag_widget.bg_button.clicked.connect(
                lambda checked=False, tag=item: self._on_item_chosen(tag)
            )
        else:
            tag_widget.bg_button.clicked.connect(
                lambda checked=False, edit_tag=item: self.on_item_edit(edit_tag)
            )

        # Connect search action
        if self._driver is not None:
            tag_widget.search_for_tag_action.triggered.connect(
                lambda checked=False, tag_id=item.id: self.search_for_tag(tag_id)
            )
            tag_widget.search_for_tag_action.setEnabled(True)
        else:
            logger.warning(
                "[TagSearchPanel] No driver was set for this TagSearchPanel. Was this on purpose?"
            )
            tag_widget.search_for_tag_action.setEnabled(False)

    @override
    def create_item(self, edit_item_panel: PanelWidget, choose_item: bool = False) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        if isinstance(edit_item_panel, BuildTagPanel):
            tag: Tag = edit_item_panel.build_tag()
            self.__lib.add_tag(
                tag, parent_ids=edit_item_panel.parent_ids, aliases=edit_item_panel.aliases
            )

            if choose_item:
                self._on_item_chosen(tag)
                self.clear_search_query()

        edit_item_panel.hide()
        self.on_search_query_changed(self.view.search_field.text())

    @override
    def edit_item(self, edit_item_panel: PanelWidget) -> None:
        # TODO: Move this to a top-level import
        from tagstudio.qt.mixed.build_tag import BuildTagPanel  # here due to circular imports

        if not isinstance(edit_item_panel, BuildTagPanel):
            return

        self.__lib.update_tag(
            tag=edit_item_panel.build_tag(),
            parent_ids=edit_item_panel.parent_ids,
            aliases=edit_item_panel.aliases,
        )
        self.update_items(self.view.search_field.text())

    def search_for_tag(self, tag_id: int) -> None:
        if self._driver is None:
            return

        self._driver.main_window.search_field.setText(f"tag_id:{tag_id}")
        self._driver.update_browsing_state(
            BrowsingState.from_tag_id(tag_id, self._driver.browsing_history.current)
        )

    @override
    def get_item_widget(self, index: int, library: Library | None) -> TagWidget:
        """Gets the item widget at a specific index."""
        # Create any new item widgets needed up to the given index
        if self.view.content_layout.count() <= index:
            # opacity_effect = QGraphicsOpacityEffect(self)
            # opacity_effect.setOpacity(0.3)
            while self.view.content_layout.count() <= index:
                tag_widget = TagWidget(tag=None, has_edit=True, has_remove=True, library=library)
                tag_widget.on_remove.connect(self.update_items)
                tag_widget.bg_button.setSizePolicy(
                    QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
                )
                tag_widget.setHidden(True)
                # if index > 0:
                #     tag_widget.setGraphicsEffect(opacity_effect)
                self.view.content_layout.addWidget(tag_widget)

        tag_widget: QWidget = self.view.content_layout.itemAt(index).widget()
        assert isinstance(tag_widget, TagWidget)
        return tag_widget

    # @override
    # def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
    #     # When Escape is pressed, focus back on the search box.
    #     # If focus is already on the search box, close the modal.
    #     pass
    #     # if event.key() in {QtCore.Qt.Key.Key_Escape, QtCore.Qt.Key.Key_Backspace, }:
    #     #     if self.search_field.hasFocus():

    #     #         self.hide()

    # @override
    # def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
    #     # When Escape is pressed, focus back on the search box.
    #     # If focus is already on the search box, close the modal.
    #     # if event.key() == QtCore.Qt.Key.Key_Escape:
    #     #     if self.search_field.hasFocus():
    #     #         self.hide()
    #     logger.info(event.key)
    #     if event.key() in {
    #         QtCore.Qt.Key.Key_Escape,
    #         QtCore.Qt.Key.Key_Enter,
    #         QtCore.Qt.Key.Key_Return,
    #     }:
    #         if self.search_field.hasFocus():
    #             logger.info("Hiding")
    #             self.hide()
    #     elif event.key() in {QtCore.Qt.Key.Key_Backspace, QtCore.Qt.Key.Key_Delete}:
    #         if self.search_field.hasFocus() and self.search_field.text() == "":
    #             # self.hide()
