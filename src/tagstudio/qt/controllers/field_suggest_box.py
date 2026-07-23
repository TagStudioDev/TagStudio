# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from typing import override
from warnings import catch_warnings

import structlog
from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy.fields import BaseFieldTemplate
from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.controllers.edit_field_template_modal import EditFieldTemplateModal
from tagstudio.qt.controllers.field_template_widget_controller import FieldTemplateWidget
from tagstudio.qt.controllers.suggest_box import SuggestBox
from tagstudio.qt.controllers.underlined_widget import UnderlinedWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelModal, PanelWidget

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class FieldSuggestBox(SuggestBox[BaseFieldTemplate]):
    def __init__(self, driver: "QtDriver", placeholder_text: str = ""):
        super().__init__(driver, placeholder_text)
        self._lib = self._driver.lib

        # Context Menu Actions
        edit_field_on_add_action = QAction(Translations["settings.edit_field_on_add"], self)
        edit_field_on_add_action.setCheckable(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.addAction(edit_field_on_add_action)
        self.layout().search_field.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.layout().search_field.addAction(edit_field_on_add_action)
        edit_field_on_add_action.setChecked(self._driver.settings.edit_field_on_add)
        edit_field_on_add_action.triggered.connect(
            lambda checked: self.toggle_edit_on_field_add(checked)
        )

    def toggle_edit_on_field_add(self, checked: bool) -> None:
        """Toggle the setting for opening the edit window after adding a field."""
        self._driver.settings.edit_field_on_add = checked
        self._driver.settings.save()

    @override
    def _on_item_create(self) -> None:
        """Creates a new field template and adds it to the currently selected entries.

        Optionally opens up an edit panel after creation and before adding to entries.
        Populates name field using current search query.
        """
        # NOTE: Unlike tags, creating new field templates will ALWAYS spawn an edit window
        # since the user needs to decide what type of field it should be before it's created.
        query: str = self.layout().search_field.text()
        panel = EditFieldTemplateModal()
        modal = PanelModal(
            panel,
            Translations["field_template.new"],
            Translations["field_template.new"],
            is_savable=True,
        )
        if query.strip():
            panel.name_field.setText(query)

        modal.saved.connect(lambda: self._create_item_from_modal(panel))
        modal.show()

    @override
    def _on_item_edit(self, item: BaseFieldTemplate) -> None:
        panel: EditFieldTemplateModal = EditFieldTemplateModal(item)
        modal: PanelModal = PanelModal(
            panel, item.name, Translations["field_template.edit"], is_savable=True
        )

        modal.saved.connect(lambda: self._edit_item(panel))
        modal.show()

    @override
    def _on_item_chosen(self, item: BaseFieldTemplate) -> None:
        self.item_chosen.emit(item)
        self.done.emit()

    @override
    def _search_items(self, query: str) -> tuple[list[BaseFieldTemplate], list[BaseFieldTemplate]]:
        if query != "":
            return self._lib.search_field_templates(name=query, limit=0), []
        else:
            return ([], [])

    @override
    def _set_item_widget(self, item: BaseFieldTemplate | None, index: int) -> None:
        """Set the field template of a field template widget at a specific index."""
        underlined_widget: UnderlinedWidget = self._get_item_widget(index, self._lib)
        field_template_widget = underlined_widget.widget
        assert isinstance(field_template_widget, FieldTemplateWidget)
        field_template_widget.has_remove = False
        field_template_widget.set_field_template(item)
        underlined_widget.setHidden(item is None)

        if item is None:
            return

        # TODO: Add tabbing to different items, and use underline to indicate which will be added
        underlined_widget.toggle_underline(index != 0)

        # Disconnect previous callbacks
        with catch_warnings(record=True):
            field_template_widget.on_edit.disconnect()
            field_template_widget.on_remove.disconnect()
            field_template_widget.on_click.disconnect()

        # Connect callbacks
        field_template_widget.on_edit.connect(lambda item_=item: self._on_item_edit(item_))
        field_template_widget.on_click.connect(
            lambda checked=False, item_=item: self._on_item_chosen(item_)
        )

    @override
    def _create_item_from_modal(self, edit_item_panel: PanelWidget) -> None:
        if isinstance(edit_item_panel, EditFieldTemplateModal):
            template: BaseFieldTemplate = edit_item_panel.build_field_template()
            self._lib.add_field_template(template)
            self._on_item_chosen(template)
            self._clear_search_query()

        edit_item_panel.hide()
        self._on_search_query_changed(self.layout().search_field.text())

    @override
    def _edit_item(self, edit_item_panel: PanelWidget) -> None:
        if not isinstance(edit_item_panel, EditFieldTemplateModal):
            return

        self._lib.update_field_template(
            edit_item_panel.old_field_type, edit_item_panel.build_field_template()
        )
        self._update_items(self.layout().search_field.text())

    @override
    def _get_item_widget(self, index: int, library: Library | None) -> UnderlinedWidget:
        """Gets the item widget at a specific index."""
        # Create any new item widgets needed up to the given index
        if self.layout().content_layout.count() <= index:
            while self.layout().content_layout.count() <= index:
                field_template_widget = FieldTemplateWidget()
                widget = UnderlinedWidget(field_template_widget)
                widget.setHidden(True)
                self.layout().content_layout.addWidget(widget)

        widget_: QWidget = self.layout().content_layout.itemAt(index).widget()
        assert isinstance(widget_, UnderlinedWidget)
        return widget_
