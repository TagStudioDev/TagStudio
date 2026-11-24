# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.tag_capsule_box import TagCapsuleBox
from tagstudio.qt.controllers.tag_search_panel import TagSearchPanel
from tagstudio.qt.entry_state import EntryState
from tagstudio.qt.views.search_panel_view import SearchPanelView
from tagstudio.qt.views.tagging_panel_view import TaggingPanelView

_STARTING_WIDTH = 240
_RECENT_TAGS_LIMIT = 20  # TODO: Make a setting


# TODO: Implement the pinned and top tags sections
class TaggingPanel(QWidget):
    """A panel of tagging tools in collapsible sections."""

    def __init__(self, library: Library, entry_state: EntryState) -> None:
        super().__init__()
        self.tag_search = TagSearchPanel(
            library,
            view=SearchPanelView(Translations["home.search_tags"]),
        )
        self.tag_search.setMinimumSize(0, 0)
        self.tag_search.layout().setContentsMargins(0, 0, 0, 0)
        self.recent_tags = TagCapsuleBox(library, entry_state)
        self.recent_tags.edit_tag_requested.connect(self.tag_search.on_item_edit)
        self.setLayout(
            TaggingPanelView(
                self.tag_search, self.tag_search.layout().search_layout, self.recent_tags
            )
        )
        section_splitter = self.layout().section_splitter
        for index, section in enumerate(section_splitter.sections[1:], start=1):
            section_splitter.toggle_collapsed(index)
            section.finish_contents()

    def focus_tag_search(self) -> None:
        """Focus the tag search field if its section is expanded."""
        if not self.layout().section_splitter.sections[0].is_collapsed:
            self.tag_search.focus_search_box(select_all=True)

    def add_recent_tags(self, tag_ids: list[int]) -> None:
        """Add these tags to the front of the recent tags, moving any that are already listed."""
        older_tag_ids = [tag_id for tag_id in self.recent_tags.tag_ids if tag_id not in tag_ids]
        self.recent_tags.set_tag_ids([*tag_ids, *older_tag_ids][:_RECENT_TAGS_LIMIT])

    @override
    def layout(self) -> TaggingPanelView:
        layout = super().layout()
        assert isinstance(layout, TaggingPanelView)
        return layout

    @override
    def sizeHint(self) -> QSize:
        return QSize(_STARTING_WIDTH, super().sizeHint().height())
