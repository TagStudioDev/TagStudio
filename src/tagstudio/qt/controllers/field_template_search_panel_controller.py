# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from warnings import catch_warnings

import structlog
from PySide6.QtCore import Signal

from tagstudio.core.library.alchemy.fields import BaseFieldTemplate
from tagstudio.core.library.alchemy.library import Library
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
        done_callback=None,
        save_callback=None,
        has_save=False,
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

    def _get_max_limit(self) -> int:
        return len(self.__lib.field_templates)

    def on_item_create(self) -> None:
        # TODO: Allow creation of field templates
        pass

    def on_item_edit(self, item: BaseFieldTemplate) -> None:
        # TODO: Allow creation of field templates
        pass

    def _on_item_remove(self, item: BaseFieldTemplate) -> None:
        if self.is_chooser:
            return

        # TODO: Allow creation of field templates
        pass

    def on_item_create_and_add(self) -> None:
        # TODO: Allow creation of field templates
        pass

    def _on_item_chosen(self, item: BaseFieldTemplate) -> None:
        self.field_template_chosen.emit(item)

    def search_items(self, query: str) -> tuple[list[BaseFieldTemplate], list[BaseFieldTemplate]]:
        return self.__lib.search_field_templates(name=query, limit=self._get_limit()[1]), []

    def set_item_widget(self, item: BaseFieldTemplate | None, index: int) -> None:
        """Set the field template of a field template widget at a specific index."""
        field_template_widget: FieldTemplateWidget = self.get_item_widget(index, self.__lib)
        field_template_widget.set_field_template(item)
        field_template_widget.setHidden(item is None)

        if item is None:
            return

        # field_template_widget.has_remove = not self.is_chooser

        # Disconnect previous callbacks
        with catch_warnings(record=True):
            # tag_widget.on_edit.disconnect()
            # tag_widget.on_remove.disconnect()
            field_template_widget.on_click.disconnect()

        # Connect callbacks
        # tag_widget.on_edit.connect(lambda edit_tag=item: self.on_item_edit(edit_tag))
        # tag_widget.on_remove.connect(lambda remove_tag=item: self._on_item_remove(remove_tag))
        field_template_widget.on_click.connect(
            lambda checked=False, tag=item: self._on_item_chosen(tag)
        )

    def create_item(self, build_item_modal: PanelModal, choose_item: bool = False) -> None:
        # TODO: Allow creation of field templates
        pass

    def edit_item(self, edit_item_panel: PanelWidget) -> None:
        # TODO: Allow creation of field templates
        pass
