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
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers import edit_tag_panel  # Module import due to circular import
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.controllers.search_panel import SearchPanel
from tagstudio.qt.views.search_panel_view import SearchPanelView
from tagstudio.qt.views.styles.stylesheets import PAD, TagShape
from tagstudio.qt.views.styles.tag_icons import tag_icon

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
        self.layout().create_from_query_button.set_is_tag(True)

    @override
    def showEvent(self, event: QShowEvent) -> None:
        # NOTE: hideEvent() removes this again, so hidden panels don't search on every tag edit
        if self._on_tags_edited not in self._lib.tag_edit_callbacks:
            self._lib.tag_edit_callbacks.append(self._on_tags_edited)
        super().showEvent(event)

    @override
    def hideEvent(self, event: QHideEvent) -> None:
        # NOTE: showEvent() adds this again, so hidden panels don't search on every tag edit
        if self._on_tags_edited in self._lib.tag_edit_callbacks:
            self._lib.tag_edit_callbacks.remove(self._on_tags_edited)
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
    def on_item_edit(self, item: Tag) -> None:
        panel = edit_tag_panel.EditTagPanel(self._lib, tag=item)
        modal: Modal = Modal(panel, Translations["tag.edit"], is_savable=True, inline_title=False)
        modal.saved.connect(lambda: self.edit_item(panel))
        modal.show()

    @override
    def _on_item_remove(self, item: Tag) -> None:
        if self._is_chooser:
            return

        if item.id in range(RESERVED_TAG_START, RESERVED_TAG_END):
            return

        message_box = QMessageBox(
            QMessageBox.Icon.Warning,
            Translations["tag.remove"],
            Translations.format("tag.confirm_delete", tag_name=self._lib.tag_display_name(item)),
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

        self._lib.remove_tag(item.id)

    @override
    def _on_item_chosen(self, item: Tag) -> None:
        self.item_chosen.emit(item.id)

    @override
    def search_items(self, query: str) -> tuple[list[Tag], list[Tag]]:
        return self._lib.search_tags(name=query, limit=-1)

    @override
    def _update_item_widgets(self) -> None:
        results_layout = self.layout().results_layout
        margins = results_layout.contentsMargins()
        margins.setLeft(PAD - (TagShape.PILL_INSET_REDUCTION if TagShape.is_pill else 0))
        results_layout.setContentsMargins(margins)
        super()._update_item_widgets()

    @override
    def set_item_widget(self, item: Tag, index: int) -> None:
        """Set the tag for a capsule widget at a specific index."""
        capsule = self.get_item_widget(index)
        capsule.set_text(self._lib.tag_display_name(item))
        capsule.set_color_group(item.color)
        capsule.set_icon(tag_icon(item.id))
        capsule.has_remove = not self._is_chooser and item.id not in range(
            RESERVED_TAG_START, RESERVED_TAG_END
        )

        # Disconnect previous callbacks
        with catch_warnings(record=True):
            capsule.on_click.disconnect()
            capsule.on_edit.disconnect()
            capsule.on_remove.disconnect()
            capsule.on_search.disconnect()

        # Connect callbacks
        capsule.on_edit.connect(lambda edit_tag=item: self.on_item_edit(edit_tag))
        capsule.on_remove.connect(lambda remove_tag=item: self._on_item_remove(remove_tag))
        if self._is_chooser:
            capsule.on_click.connect(lambda tag=item: self._on_item_chosen(tag))
        else:
            capsule.on_click.connect(lambda edit_tag=item: self.on_item_edit(edit_tag))
        capsule.on_search.connect(lambda tag_id=item.id: self.search_for_tag.emit(tag_id))

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
            search_label=Translations["tag.search_for_tag"],
            is_tag=True,
            is_stretched=True,
        )
