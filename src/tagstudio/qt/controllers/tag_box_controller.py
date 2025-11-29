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
    __mixed_only: bool = False

    def __init__(self, title: str, driver: "QtDriver"):
        super().__init__(title, driver)
        self.__driver = driver

    def set_entries(self, entries: list[int]) -> None:
        self.__entries = entries

    def set_mixed_only(self, value: bool) -> None:
        """If True, all tags in this widget are treated as non-shared (grayed out)."""
        self.__mixed_only = value

    def set_tags(self, tags):  # type: ignore[override]
        """Render tags; optionally gray out those that are not shared across entries."""
        tags_ = list(tags)

        # When mixed_only is set, all tags in this widget are considered non-shared.
        shared_tag_ids: set[int] = set()
        if not self.__mixed_only and self.__entries:
            tag_ids = [t.id for t in tags_]
            tag_entries = self.__driver.lib.get_tag_entries(tag_ids, self.__entries)
            required = set(self.__entries)
            for tag_id, entries in tag_entries.items():
                if set(entries) >= required:
                    shared_tag_ids.add(tag_id)

        super().set_tags(tags_)

        # Gray out tags that are not shared across all selected entries.
        from tagstudio.qt.mixed.tag_widget import TagWidget  # local import to avoid cycles

        layout = getattr(self, "_TagBoxWidgetView__root_layout", None)
        if layout is not None:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                widget = item.widget()
                if isinstance(widget, TagWidget) and widget.tag:
                    if self.__mixed_only or widget.tag.id not in shared_tag_ids:
                        widget.setEnabled(False)

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
