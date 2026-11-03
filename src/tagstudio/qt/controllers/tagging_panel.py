# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.tag_search_panel import TagSearchPanel
from tagstudio.qt.views.search_panel_view import SearchPanelView
from tagstudio.qt.views.tagging_panel_view import TaggingPanelView

_STARTING_WIDTH = 240


# TODO: Implement the pinned, recent, and top tags sections
class TaggingPanel(QWidget):
    """A panel of tagging tools in collapsible sections."""

    def __init__(self, library: Library) -> None:
        super().__init__()
        self.tag_search = TagSearchPanel(
            library,
            view=SearchPanelView(Translations["home.search_tags"]),
        )
        self.tag_search.setMinimumSize(0, 0)
        self.tag_search.layout().setContentsMargins(0, 0, 0, 0)
        self.setLayout(TaggingPanelView(self.tag_search, self.tag_search.layout().search_layout))
        section_splitter = self.layout().section_splitter
        for index, section in enumerate(section_splitter.sections[1:], start=1):
            section_splitter.toggle_collapsed(index)
            section.finish_contents()

    @override
    def layout(self) -> TaggingPanelView:
        layout = super().layout()
        assert isinstance(layout, TaggingPanelView)
        return layout

    @override
    def sizeHint(self) -> QSize:
        return QSize(_STARTING_WIDTH, super().sizeHint().height())
