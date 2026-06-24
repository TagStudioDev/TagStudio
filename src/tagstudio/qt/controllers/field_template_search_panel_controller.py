# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from typing import override
from warnings import catch_warnings

import structlog
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox

from tagstudio.core.library.alchemy.fields import BaseFieldTemplate
from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.controllers.edit_field_template_modal import EditFieldTemplateModal
from tagstudio.qt.controllers.field_template_widget_controller import FieldTemplateWidget
from tagstudio.qt.controllers.search_panel_controller import SearchPanel
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.field_template_search_panel_view import FieldTemplateSearchPanelView
from tagstudio.qt.views.panel_modal import PanelModal, PanelWidget

logger = structlog.get_logger(__name__)


class FieldTemplateSearchModal(PanelModal):
    def __init__(
        self,
        library: Library,
        is_field_template_chooser: bool = True,
        done_callback: Callable[..., None] | None = None,
        save_callback: Callable[..., None] | None = None,
        has_save: bool = False,
    ) -> None:
        self.search_panel: FieldTemplateSearchPanel = FieldTemplateSearchPanel(
            library,
            is_field_template_chooser,
            view=FieldTemplateSearchPanelView(is_field_template_chooser),
        )
        super().__init__(
            self.search_panel,
            Translations["field.add.plural"],
            done_callback=done_callback,
            save_callback=save_callback,
            has_save=has_save,
        )


class FieldTemplateSearchPanel(SearchPanel[BaseFieldTemplate]):
    field_template_chosen = Signal(object)

    def __init__(
        self,
        library: Library,
        is_field_template_chooser: bool = True,
        view: FieldTemplateSearchPanelView | None = None,
    ) -> None:
        super().__init__(
            view=view or FieldTemplateSearchPanelView(is_field_template_chooser),
            exclude=[],
            is_chooser=is_field_template_chooser,
        )
        self.__lib = library

        self._unlimited_limit_item_label = Translations["field_template.all_field_templates"]
        self._create_and_add_button_label_key = "field_template.create_add"

    @override
    def _get_max_limit(self) -> int:
        return len(self.__lib.field_templates)

    @override
    def on_item_create(self) -> None:
        # TODO: Allow creation of field templates
        pass

    @override
    def on_item_edit(self, item: BaseFieldTemplate) -> None:

        panel: EditFieldTemplateModal = EditFieldTemplateModal(item)
        modal: PanelModal = PanelModal(
            panel,
            item.name,
            Translations["field_template.edit"],
            has_save=True,
        )

        modal.saved.connect(lambda: self.edit_item(panel))
        modal.show()

    @override
    def _on_item_remove(self, item: BaseFieldTemplate) -> None:

        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            Translations["field_template.delete"],
            Translations.format("field_template.confirm_delete", field_template_name=item.name),
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )

        result = message_box.exec()

        if result != QMessageBox.StandardButton.Ok:
            return

        self.__lib.remove_field_template(item)
        self.update_items(self.get_search_query())

    @override
    def on_item_create_and_add(self) -> None:
        """Opens "Create Field Template" panel to create a new field template.

        Populates name field using current search query.
        """
        query: str = self.get_search_query()
        logger.info("[FieldTemplateSearch] Create and Add Field Template", name=query)

        panel: EditFieldTemplateModal = EditFieldTemplateModal()
        modal: PanelModal = PanelModal(
            panel,
            Translations["field_template.new"],
            Translations["field.add"],
            has_save=True,
        )

        if query.strip():
            panel.name_field.setText(query)

        modal.saved.connect(lambda: self.create_item(panel, choose_item=True))
        modal.show()

    @override
    def _on_item_chosen(self, item: BaseFieldTemplate) -> None:
        self.field_template_chosen.emit(item)

    @override
    def search_items(self, query: str) -> tuple[list[BaseFieldTemplate], list[BaseFieldTemplate]]:
        return self.__lib.search_field_templates(name=query, limit=self._get_limit()[1]), []

    @override
    def set_item_widget(self, item: BaseFieldTemplate | None, index: int) -> None:
        """Set the field template of a field template widget at a specific index."""
        field_template_widget: FieldTemplateWidget = self.get_item_widget(index, self.__lib)
        field_template_widget.set_field_template(item)
        field_template_widget.setHidden(item is None)

        if item is None:
            return

        # Disconnect previous callbacks
        with catch_warnings(record=True):
            field_template_widget.on_edit.disconnect()
            field_template_widget.on_remove.disconnect()
            field_template_widget.on_click.disconnect()

        # Connect callbacks
        field_template_widget.on_edit.connect(lambda item_=item: self.on_item_edit(item_))
        field_template_widget.on_remove.connect(lambda item_=item: self._on_item_remove(item_))
        field_template_widget.on_click.connect(
            lambda checked=False, item_=item: self._on_item_chosen(item_)
        )

    @override
    def create_item(self, edit_item_panel: PanelWidget, choose_item: bool = False) -> None:

        if isinstance(edit_item_panel, EditFieldTemplateModal):
            template: BaseFieldTemplate = edit_item_panel.build_field_template()
            self.__lib.add_field_template(template)

            if choose_item:
                self._on_item_chosen(template)
                self.clear_search_query()

        edit_item_panel.hide()
        self.on_search_query_changed(self.get_search_query())

    @override
    def edit_item(self, edit_item_panel: PanelWidget) -> None:
        if not isinstance(edit_item_panel, EditFieldTemplateModal):
            return

        self.__lib.update_field_template(
            edit_item_panel.old_field_type, edit_item_panel.build_field_template()
        )
        self.update_items(self.search_field.text())
