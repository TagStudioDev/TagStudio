# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Iterable
from functools import partial
from typing import TYPE_CHECKING, override

import structlog
from PySide6.QtCore import Signal

from tagstudio.core.enums import TagClickActionOption
from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.tag_cache import CachedTag
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.edit_tag_panel import EditTagPanel
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.tiles.tile_data import TileData
from tagstudio.qt.views.layouts.capsule_flow_layout import CapsuleFlowLayout
from tagstudio.qt.views.styles.tag_icons import tag_icon

if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)


class TagData(TileData):
    """An inner widget for tags that go in a Tile widget."""

    on_update = Signal()

    def __init__(self, title: str, driver: QtDriver):
        self._driver = driver
        self._lib = driver.lib
        self._entries: list[int] = []
        super().__init__(title, CapsuleFlowLayout())
        self.setObjectName("tag_data")

    @override
    def layout(self) -> CapsuleFlowLayout:
        layout = super().layout()
        assert isinstance(layout, CapsuleFlowLayout)
        return layout

    def set_entries(self, entries: list[int]) -> None:
        self._entries = entries

    def set_tags(self, tags: Iterable[CachedTag]) -> None:
        tags_ = sorted(list(tags), key=lambda tag: self._lib.tag_display_name(tag).casefold())
        logger.info("[TagData] Tags:", tags=tags)

        layout = self.layout()
        while item := layout.takeAt(0):
            if widget := item.widget():
                widget.hide()
                widget.deleteLater()

        for tag in tags_:
            capsule = Capsule(
                has_edit=True,
                has_remove=True,
                search_label=Translations["tag.search_for_tag"],
                is_tag=True,
            )
            capsule.set_text(self._lib.tag_display_name(tag))
            capsule.set_color_group(tag.color)
            capsule.set_icon(tag_icon(tag.id))
            capsule.on_click.connect(lambda t=tag: self._on_click(t))
            capsule.on_remove.connect(lambda t=tag: self._on_remove(t))
            capsule.on_edit.connect(lambda t=tag: self._on_edit(t))
            capsule.on_search.connect(lambda t=tag: self._on_search(t))
            layout.addWidget(capsule)
            capsule.show()

    def _on_click(self, tag: CachedTag) -> None:
        match self._driver.settings.tag_click_action:
            case TagClickActionOption.OPEN_EDIT:
                self._on_edit(tag)
            case TagClickActionOption.SET_SEARCH:
                self._driver.navigator.update_browsing_state(
                    BrowsingState.from_tag_id(
                        tag.id, self._driver.navigator.browsing_history.current
                    )
                )
            case TagClickActionOption.ADD_TO_SEARCH:
                # NOTE: modifying the ast and then setting that would be nicer
                #       than this string manipulation, but also much more complex,
                #       due to needing to implement a visitor that turns an AST to a string
                #       So if that exists when you read this, change the following accordingly.
                current = self._driver.navigator.browsing_history.current
                suffix = unwrap(
                    BrowsingState.from_tag_id(
                        tag.id, self._driver.navigator.browsing_history.current
                    ).query
                )
                self._driver.navigator.update_browsing_state(
                    current.with_search_query(
                        f"{current.query} {suffix}" if current.query else suffix
                    )
                )

    def _on_remove(self, tag: CachedTag) -> None:
        logger.info("[TagData] remove_tag", selected=self._entries)

        self._driver.entry_state.remove_tags(self._entries, tag.id)

    def _on_edit(self, tag: CachedTag) -> None:
        tag_to_edit = self._lib.get_tag(tag.id)
        if tag_to_edit is None:
            return
        edit_tag_panel = EditTagPanel(self._driver.lib, tag=tag_to_edit)

        edit_modal = Modal(
            edit_tag_panel, Translations["tag.edit"], is_savable=True, inline_title=False
        )
        edit_modal.saved.connect(partial(self._update_tag_callback, edit_tag_panel))
        edit_modal.show()

    def _update_tag_callback(self, edit_tag_panel: EditTagPanel):
        self._driver.lib.update_tag(
            edit_tag_panel.build_tag(),
            parent_ids=set(edit_tag_panel.parent_ids),
            aliases=set(edit_tag_panel.aliases),
            exclusion_ids=set(edit_tag_panel.exclusion_ids),
        )
        self.on_update.emit()

    def _on_search(self, tag: CachedTag) -> None:
        self._driver.main_window.search_bar.set_query(f"tag_id:{tag.id}")
        self._driver.navigator.update_browsing_state(
            BrowsingState.from_tag_id(tag.id, self._driver.navigator.browsing_history.current)
        )
