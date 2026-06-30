# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import override

from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.controllers.field_template_widget_controller import FieldTemplateWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.search_panel_view import SearchPanelView


class FieldTemplateSearchPanelView(SearchPanelView):
    def __init__(self, is_field_template_chooser: bool) -> None:
        super().__init__(is_field_template_chooser)

        self.search_field.setPlaceholderText(Translations["home.search_field_templates"])
        self.create_button.setText(Translations["field_template.create"])

    @override
    def get_item_widget(self, index: int, library: Library | None) -> FieldTemplateWidget:
        """Gets the item widget at a specific index."""
        # Create any new item widgets needed up to the given index
        if self._scroll_layout.count() <= index:
            while self._scroll_layout.count() <= index:
                pad_field_template_widget = FieldTemplateWidget()
                pad_field_template_widget.setHidden(True)
                self._scroll_layout.addWidget(pad_field_template_widget)

        field_template_widget: QWidget = self._scroll_layout.itemAt(index).widget()
        assert isinstance(field_template_widget, FieldTemplateWidget)
        return field_template_widget
