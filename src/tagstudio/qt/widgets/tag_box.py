# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

import structlog
from PySide6.QtCore import Signal

from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.flowlayout import FlowLayout
from tagstudio.qt.modals.build_tag import BuildTagPanel
from tagstudio.qt.widgets.fields import FieldWidget
from tagstudio.qt.widgets.panel import PanelModal
from tagstudio.qt.widgets.tag import TagWidget

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class TagBoxWidget(FieldWidget):
    updated = Signal()
    error_occurred = Signal(Exception)

    def __init__(
        self,
        tags: set[Tag],
        title: str,
        driver: "QtDriver",
    ) -> None:
        super().__init__(title)

        self.tags: set[Tag] = tags
        self.driver = (
            driver  # Used for creating tag click callbacks that search entries for that tag.
        )
        self.setObjectName("tagBox")
        self.base_layout = FlowLayout()
        self.base_layout.enable_grid_optimizations(value=False)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.base_layout)

        self.set_tags(self.tags)

    def set_tags(self, tags: typing.Iterable[Tag]):
        tags_ = sorted(list(tags), key=lambda tag: self.driver.lib.tag_display_name(tag.id))
        logger.info("[TagBoxWidget] Tags:", tags=tags)
        while self.base_layout.itemAt(0):
            self.base_layout.takeAt(0).widget().deleteLater()

        for tag in tags_:
            tag_widget = TagWidget(tag, library=self.driver.lib, has_edit=True, has_remove=True)
            tag_widget.on_click.connect(lambda t=tag: self.edit_tag(t))

            tag_widget.on_remove.connect(
                lambda tag_id=tag.id: (
                    self.remove_tag(tag_id),
                    self.driver.preview_panel.update_widgets(update_preview=False),
                )
            )
            tag_widget.on_edit.connect(lambda t=tag: self.edit_tag(t))

            tag_widget.search_for_tag_action.triggered.connect(
                lambda checked=False, tag_id=tag.id: (
                    self.driver.main_window.searchField.setText(f"tag_id:{tag_id}"),
                    self.driver.update_browsing_state(BrowsingState.from_tag_id(tag_id)),
                )
            )

            self.base_layout.addWidget(tag_widget)

    def edit_tag(self, tag: Tag):
        assert isinstance(tag, Tag), f"tag is {type(tag)}"
        build_tag_panel = BuildTagPanel(self.driver.lib, tag=tag)

        self.edit_modal = PanelModal(
            build_tag_panel,
            self.driver.lib.tag_display_name(tag.id),
            "Edit Tag",
            done_callback=lambda: self.driver.preview_panel.update_widgets(update_preview=False),
            has_save=True,
        )
        # TODO - this was update_tag()
        self.edit_modal.saved.connect(
            lambda: self.driver.lib.update_tag(
                build_tag_panel.build_tag(),
                parent_ids=set(build_tag_panel.parent_ids),
                alias_names=set(build_tag_panel.alias_names),
                alias_ids=set(build_tag_panel.alias_ids),
            )
        )
        self.edit_modal.show()

    def remove_tag(self, tag_id: int):
        logger.info(
            "[TagBoxWidget] remove_tag",
            selected=self.driver.selected,
        )

        for entry_id in self.driver.selected:
            self.driver.lib.remove_tags_from_entries(entry_id, tag_id)

        self.updated.emit()
