# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from functools import partial
from typing import TYPE_CHECKING, override

import structlog
from PySide6.QtCore import Signal

from tagstudio.core.enums import TagClickActionOption
from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.build_tag import BuildTagPanel
from tagstudio.qt.views.panel_modal import PanelModal
from tagstudio.qt.views.tag_box_view import TagBoxWidgetView

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class TagBoxWidget(TagBoxWidgetView):
    on_update = Signal()

    __entries: list[int] = []

    def __init__(self, title: str, driver: "QtDriver"):
        super().__init__(title, driver)
        self.__driver = driver

    def set_entries(self, entries: list[int]) -> None:
        self.__entries = entries

    @override
    def _on_click(self, tag: Tag) -> None:
        match self.__driver.settings.tag_click_action:
            case TagClickActionOption.OPEN_EDIT:
                self._on_edit(tag)
            case TagClickActionOption.SET_SEARCH:
                self.__driver.update_browsing_state(
                    BrowsingState.from_tag_id(tag.id, self.__driver.browsing_history.current)
                )
            case TagClickActionOption.ADD_TO_SEARCH:
                # NOTE: modifying the ast and then setting that would be nicer
                #       than this string manipulation, but also much more complex,
                #       due to needing to implement a visitor that turns an AST to a string
                #       So if that exists when you read this, change the following accordingly.
                current = self.__driver.browsing_history.current
                suffix = unwrap(
                    BrowsingState.from_tag_id(tag.id, self.__driver.browsing_history.current).query
                )
                self.__driver.update_browsing_state(
                    current.with_search_query(
                        f"{current.query} {suffix}" if current.query else suffix
                    )
                )

    @override
    def _on_remove(self, tag: Tag) -> None:
        logger.info(
            "[TagBoxWidget] remove_tag",
            selected=self.__entries,
        )

        for entry_id in self.__entries:
            self.__driver.lib.remove_tags_from_entries(entry_id, tag.id)

        self.on_update.emit()

    @override
    def _on_edit(self, tag: Tag) -> None:
        build_tag_panel = BuildTagPanel(self.__driver.lib, tag=tag)

        edit_modal = PanelModal(
            build_tag_panel,
            self.__driver.lib.tag_display_name(tag),
            "Edit Tag",
            is_savable=True,
        )
        edit_modal.saved.connect(partial(self._update_tag_callback, build_tag_panel))
        edit_modal.show()

    def _update_tag_callback(self, build_tag_panel: BuildTagPanel):
        self.__driver.lib.update_tag(
            build_tag_panel.build_tag(),
            parent_ids=set(build_tag_panel.parent_ids),
            aliases=set(build_tag_panel.aliases),
        )
        self.on_update.emit()

    @override
    def _on_search(self, tag: Tag) -> None:
        self.__driver.main_window.search_field.setText(f"tag_id:{tag.id}")
        self.__driver.update_browsing_state(
            BrowsingState.from_tag_id(tag.id, self.__driver.browsing_history.current)
        )
