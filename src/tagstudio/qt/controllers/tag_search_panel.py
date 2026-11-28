# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override
from warnings import catch_warnings

import structlog
from PySide6.QtCore import Signal
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import QMessageBox

from tagstudio.core.constants import RESERVED_TAG_END, RESERVED_TAG_START
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers import edit_tag_panel  # Module import due to circular import
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.controllers.search_panel import SearchPanel
from tagstudio.qt.tag_lists_state import TagListsState
from tagstudio.qt.views.search_panel_view import SearchPanelView
from tagstudio.qt.views.styles.stylesheets import PAD, TagShape
from tagstudio.qt.views.styles.tag_icons import tag_icon

logger = structlog.get_logger(__name__)


class TagSearchPanel(SearchPanel[int]):
    search_for_tag = Signal(int)
    remove_tag_requested = Signal(int)
    _tags_edited = Signal(set)

    def __init__(
        self,
        library: Library,
        exclude: list[int] | None = None,
        is_chooser: bool = True,
        view: SearchPanelView | None = None,
        tag_lists_state: TagListsState | None = None,
    ):
        super().__init__(
            view=view or SearchPanelView(Translations["home.search_tags"], is_chooser=is_chooser),
            exclude=exclude,
            is_chooser=is_chooser,
        )
        self._lib = library
        self._tag_lists_state = tag_lists_state
        self.layout().create_from_query_button.set_is_tag(True)
        self._tags_edited.connect(self._on_tags_edited)
        self.restyle()

    def restyle(self) -> None:
        """Style the results' inset to match the tag shape."""
        self.layout().results_box.set_content_inset(TagShape.content_inset(PAD))

    @override
    def showEvent(self, event: QShowEvent) -> None:
        # NOTE: hideEvent() removes this again, so hidden panels don't search on every tag edit
        if self._tags_edited.emit not in self._lib.tag_edit_callbacks:
            self._lib.tag_edit_callbacks.append(self._tags_edited.emit)
        super().showEvent(event)

    @override
    def hideEvent(self, event: QHideEvent) -> None:
        # NOTE: showEvent() adds this again, so hidden panels don't search on every tag edit
        if self._tags_edited.emit in self._lib.tag_edit_callbacks:
            self._lib.tag_edit_callbacks.remove(self._tags_edited.emit)
        super().hideEvent(event)

    def _on_tags_edited(self, tag_ids: set[int]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Search again after tags are edited or deleted."""
        self.update_items(self.get_search_query())

    @override
    def on_item_create(self) -> None:
        """Opens panel to create a new tag.

        Populates name field using current search query.
        """
        query: str = self.get_search_query()
        panel = edit_tag_panel.EditTagPanel(self._lib)
        modal: Modal = Modal(
            panel,
            Translations["tag.new"],
            Translations["tag.new"],
            is_savable=True,
        )

        if query.strip():
            panel.set_name(query)

        modal.saved.connect(lambda: self.create_item(panel))
        modal.show()

    @override
    def on_item_edit(self, item: int) -> None:
        tag = self._lib.get_tag(item)
        if tag is None:
            return
        panel = edit_tag_panel.EditTagPanel(self._lib, tag=tag)
        modal: Modal = Modal(panel, Translations["tag.edit"], is_savable=True, inline_title=False)
        modal.saved.connect(lambda: self.edit_item(panel))
        modal.show()

    @override
    def _on_item_remove(self, item: int) -> None:
        if self._is_chooser:
            return

        if item in range(RESERVED_TAG_START, RESERVED_TAG_END):
            return

        tag = self._lib.get_cached_tag(item)
        if tag is None:
            return

        message_box = QMessageBox(
            QMessageBox.Icon.Warning,
            Translations["tag.remove"],
            Translations.format("tag.confirm_delete", tag_name=self._lib.tag_display_name(tag)),
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        unwrap(message_box.button(QMessageBox.StandardButton.Ok)).setText(
            Translations["generic.delete_alt"]
        )
        unwrap(message_box.button(QMessageBox.StandardButton.Cancel)).setText(
            Translations["generic.cancel_alt"]
        )
        message_box.setDefaultButton(QMessageBox.StandardButton.Cancel)

        result = message_box.exec()

        if result != QMessageBox.StandardButton.Ok:
            return

        self.remove_tag_requested.emit(item)

    @override
    def _on_item_chosen(self, item: int) -> None:
        self.item_chosen.emit(item)

    @override
    def search_items(self, query: str | None) -> list[int]:
        return [tag_id for tag_id in self._lib.search_tags(query) if tag_id not in self._excluded]

    @override
    def set_item_widget(self, item: int, index: int) -> None:
        """Set the tag for a capsule widget at a specific index."""
        capsule = self.get_item_widget(index)
        tag = self._lib.get_cached_tag(item)
        capsule.setHidden(tag is None)
        if tag is None:
            return
        capsule.set_text(self._lib.tag_display_name(tag))
        capsule.set_color_group(tag.color)
        capsule.set_icon(tag_icon(item))
        capsule.has_remove = not self._is_chooser and item not in range(
            RESERVED_TAG_START, RESERVED_TAG_END
        )

        # Disconnect previous callbacks
        with catch_warnings(record=True):
            capsule.on_click.disconnect()
            capsule.on_context_menu.disconnect()
            capsule.on_edit.disconnect()
            capsule.on_pin.disconnect()
            capsule.on_remove.disconnect()
            capsule.on_search.disconnect()

        # Connect callbacks
        if (tag_lists_state := self._tag_lists_state) is not None:
            capsule.on_context_menu.connect(
                lambda tag_id=item: capsule.set_pinned(tag_lists_state.is_pinned(tag_id))
            )
            capsule.on_pin.connect(
                lambda is_pinned, tag_id=item: tag_lists_state.set_pinned(tag_id, is_pinned)
            )
        capsule.on_edit.connect(lambda tag_id=item: self.on_item_edit(tag_id))
        capsule.on_remove.connect(lambda tag_id=item: self._on_item_remove(tag_id))
        if self._is_chooser:
            capsule.on_click.connect(lambda tag_id=item: self._on_item_chosen(tag_id))
        else:
            capsule.on_click.connect(lambda tag_id=item: self.on_item_edit(tag_id))
        capsule.on_search.connect(lambda tag_id=item: self.search_for_tag.emit(tag_id))

    @override
    def create_item(self, edit_item_panel: ModalContent) -> None:
        if isinstance(edit_item_panel, edit_tag_panel.EditTagPanel):
            self._lib.add_tag(
                edit_item_panel.build_tag(),
                parent_ids=edit_item_panel.parent_ids,
                aliases=edit_item_panel.aliases,
                exclusion_ids=edit_item_panel.exclusion_ids,
            )

        edit_item_panel.hide()
        self.on_search_query_changed(self.get_search_query())

    @override
    def edit_item(self, edit_item_panel: ModalContent) -> None:
        if not isinstance(edit_item_panel, edit_tag_panel.EditTagPanel):
            return

        self._lib.update_tag(
            tag=edit_item_panel.build_tag(),
            parent_ids=edit_item_panel.parent_ids,
            aliases=edit_item_panel.aliases,
            exclusion_ids=edit_item_panel.exclusion_ids,
        )

    @override
    def _new_item_widget(self) -> Capsule:
        return Capsule(
            has_edit=True,
            has_remove=True,
            has_pin=self._tag_lists_state is not None,
            search_label=Translations["tag.search_for_tag"],
            is_tag=True,
            is_stretched=True,
        )
