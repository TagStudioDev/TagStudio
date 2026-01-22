# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


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
    def _on_click(self, tag: Tag) -> None:  # type: ignore[misc]
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
    def _on_remove(self, tag: Tag) -> None:  # type: ignore[misc]
        logger.info(
            "[TagBoxWidget] remove_tag",
            selected=self.__entries,
        )

        for entry_id in self.__entries:
            self.__driver.lib.remove_tags_from_entries(entry_id, tag.id)

        group_by_tag_id = self.__driver.browsing_history.current.group_by_tag_id
        if group_by_tag_id is not None:
            relevant_tag_ids = self.__driver.lib.get_grouping_tag_ids(group_by_tag_id)
            if tag.id in relevant_tag_ids:
                self.__driver.update_browsing_state()

        self.on_update.emit()

    @override
    def _on_edit(self, tag: Tag) -> None:  # type: ignore[misc]
        build_tag_panel = BuildTagPanel(self.__driver.lib, tag=tag)

        edit_modal = PanelModal(
            build_tag_panel,
            self.__driver.lib.tag_display_name(tag),
            "Edit Tag",
            done_callback=self.on_update.emit,
            has_save=True,
        )
        # TODO - this was update_tag()
        edit_modal.saved.connect(
            lambda: self.__driver.lib.update_tag(
                build_tag_panel.build_tag(),
                parent_ids=set(build_tag_panel.parent_ids),
                alias_names=set(build_tag_panel.alias_names),
                alias_ids=set(build_tag_panel.alias_ids),
            )
        )
        edit_modal.show()

    @override
    def _on_search(self, tag: Tag) -> None:  # type: ignore[misc]
        self.__driver.main_window.search_field.setText(f"tag_id:{tag.id}")
        self.__driver.update_browsing_state(
            BrowsingState.from_tag_id(tag.id, self.__driver.browsing_history.current)
        )
