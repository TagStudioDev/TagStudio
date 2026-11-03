# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.collapsible_section import CollapsibleSection
from tagstudio.qt.controllers.inset_frame import InsetFrame
from tagstudio.qt.controllers.section_splitter import SectionSplitter
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.stylesheets import WIN_PAD

_TAG_LIST_MIN_HEIGHT = 72  # Placeholder height of the pinned, recent, and top tag lists


class TaggingPanelView(QVBoxLayout):
    def __init__(self, tag_search: QWidget, tag_search_row: QHBoxLayout) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, WIN_PAD)
        rm = ResourceManager()

        self.section_splitter = SectionSplitter(
            [
                CollapsibleSection(
                    rm.tag_search_icon_solid,
                    Translations["panel.tagging.tag_search"],
                    tag_search,
                    caret_row=tag_search_row,
                ),
                self._placeholder_section(
                    rm.pinned_tags_icon_solid, Translations["panel.tagging.pinned_tags"]
                ),
                self._placeholder_section(
                    rm.recent_tags_icon_solid, Translations["panel.tagging.recent_tags"]
                ),
                self._placeholder_section(
                    rm.top_tags_icon_solid, Translations["panel.tagging.top_tags"]
                ),
            ]
        )
        self.addWidget(self.section_splitter, stretch=1)
        self.addStretch()

    def _placeholder_section(self, svg: bytes, title: str) -> CollapsibleSection:
        tag_list = InsetFrame()
        tag_list.setMinimumHeight(_TAG_LIST_MIN_HEIGHT)
        return CollapsibleSection(svg, title, tag_list)
