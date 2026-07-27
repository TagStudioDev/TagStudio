# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import override

from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.search_panel_view import SearchPanelView


class TagSearchPanelView(SearchPanelView):
    def __init__(self, is_tag_chooser: bool) -> None:
        super().__init__(is_tag_chooser)

        self.search_field.setPlaceholderText(Translations["home.search_tags"])
        self.create_button.setText(Translations["tag.create"])

    @override
    def get_item_widget(self, index: int, library: Library | None) -> TagWidget:
        """Gets the item widget at a specific index."""
        # Create any new item widgets needed up to the given index
        if self._scroll_layout.count() <= index:
            while self._scroll_layout.count() <= index:
                pad_tag_widget = TagWidget(
                    tag=None, has_edit=True, has_remove=True, library=library
                )
                pad_tag_widget.setHidden(True)
                self._scroll_layout.addWidget(pad_tag_widget)

        tag_widget: QWidget = self._scroll_layout.itemAt(index).widget()
        assert isinstance(tag_widget, TagWidget)
        return tag_widget
