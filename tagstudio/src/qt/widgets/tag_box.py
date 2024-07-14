# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
import typing

import structlog
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QPushButton

from src.core.constants import TAG_FAVORITE, TAG_ARCHIVED
from src.core.library import Library, Entry, Tag
from src.core.library.alchemy.enums import FilterState
from src.core.library.alchemy.fields import TagBoxField
from src.qt.flowlayout import FlowLayout
from src.qt.widgets.fields import FieldWidget
from src.qt.widgets.tag import TagWidget
from src.qt.widgets.panel import PanelModal
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.modals.tag_search import TagSearchPanel

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class TagBoxWidget(FieldWidget):
    updated = Signal()

    def __init__(
        self,
        item: Entry,
        title: str,
        # field_index: int,
        tags: list[Tag],  # tags from TagBoxField model
        driver: "QtDriver",
    ) -> None:
        super().__init__(title)

        self.item = item
        self.driver = driver  # Used for creating tag click callbacks that search entries for that tag.
        # self.field_index = field_index
        self.tags = tags
        self.setObjectName("tagBox")
        self.base_layout = FlowLayout()
        self.base_layout.setGridEfficiency(False)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.base_layout)

        self.add_button = QPushButton()
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setMinimumSize(23, 23)
        self.add_button.setMaximumSize(23, 23)
        self.add_button.setText("+")
        self.add_button.setStyleSheet(
            f"QPushButton{{"
            f"background: #1e1e1e;"
            f"color: #FFFFFF;"
            f"font-weight: bold;"
            f"border-color: #333333;"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width:{math.ceil(self.devicePixelRatio())}px;"
            f"padding-bottom: 5px;"
            f"font-size: 20px;"
            f"}}"
            f"QPushButton::hover"
            f"{{"
            f"border-color: #CCCCCC;"
            f"background: #555555;"
            f"}}"
        )
        tsp = TagSearchPanel(self.driver.lib)
        tsp.tag_chosen.connect(lambda x: self.add_tag_callback(x))
        self.add_modal = PanelModal(tsp, title, "Add Tags")
        self.add_button.clicked.connect(
            lambda: (
                tsp.update_tags(),
                self.add_modal.show(),  # type: ignore[func-returns-value]
            )
        )

        self.set_tags(tags)

    def set_item(self, item):
        self.item = item

    def set_tags(self, tags: list[Tag]):
        is_recycled = False
        if self.base_layout.itemAt(0):
            while self.base_layout.itemAt(0) and self.base_layout.itemAt(1):
                self.base_layout.takeAt(0).widget().deleteLater()
            is_recycled = True

        for tag in tags:
            tw = TagWidget(tag, True, True)
            tw.on_click.connect(
                lambda tag_id=tag.id: (
                    print("tag widget clicked on_click emited", tag_id),
                    self.driver.main_window.searchField.setText(f"tag_id:{tag_id}"),
                    self.driver.filter_items(FilterState(id=tag_id)),  # type: ignore[func-returns-value]
                )
            )

            tw.on_remove.connect(lambda tag_id=tag.id: self.remove_tag(tag_id))
            tw.on_edit.connect(lambda tag_id=tag.id: self.edit_tag(tag_id))
            self.base_layout.addWidget(tw)
        self.tags = tags

        # Move or add the '+' button.
        if is_recycled:
            self.base_layout.addWidget(self.base_layout.takeAt(0).widget())
        else:
            self.base_layout.addWidget(self.add_button)

        # Handles an edge case where there are no more tags and the '+' button
        # doesn't move all the way to the left.
        if self.base_layout.itemAt(0) and not self.base_layout.itemAt(1):
            self.base_layout.update()

    def edit_tag(self, tag_id: int):
        btp = BuildTagPanel(self.driver.lib, tag_id)
        # btp.on_edit.connect(lambda x: self.edit_tag_callback(x))
        tag = self.driver.lib.get_tag(tag_id)
        self.edit_modal = PanelModal(
            btp,
            tag.name,
            "Edit Tag",
            done_callback=self.driver.preview_panel.update_widgets,
            has_save=True,
        )
        # self.edit_modal.widget.update_display_name.connect(lambda t: self.edit_modal.title_widget.setText(t))
        # TODO - this was update_tag()
        self.edit_modal.saved.connect(lambda: self.driver.lib.add_tag(btp.build_tag()))
        # panel.tag_updated.connect(lambda tag: self.lib.update_tag(tag))
        self.edit_modal.show()

    def add_tag_callback(self, tag_id: int):
        logger.info("add_tag_callback", tag_id=tag_id, selected=self.driver.selected)

        for idx in self.driver.selected:
            entry: Entry = self.driver.frame_content[idx]

            # TODO - add tag to correct field
            tag_field: TagBoxField = entry.tag_box_fields[0]

            tag = self.driver.lib.get_tag(tag_id=tag_id)

            tag_field.tags.add(tag)

            self.updated.emit()

        if tag_id in (TAG_FAVORITE, TAG_ARCHIVED):
            self.driver.update_badges()

    def edit_tag_callback(self, tag):
        self.driver.lib.update_tag(tag)

    def remove_tag(self, tag_id: int):
        logger.info("remove_tag", selected=self.driver.selected, field=self.field)
        assert self.driver.selected

        for grid_idx in self.driver.selected:
            entry = self.driver.frame_content[grid_idx]
            # TODO - remove tag from correct field
            assert entry.fields
            tag_field = entry.fields[0]

            self.driver.lib.remove_field_tag(tag_field, tag_id)

            self.updated.emit()

        if tag_id in (TAG_FAVORITE, TAG_ARCHIVED):
            self.driver.update_badges()
