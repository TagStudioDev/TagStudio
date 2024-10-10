# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
import typing

import structlog
from PySide6.QtCore import QObject, QStringListModel, Qt, Signal
from PySide6.QtWidgets import QCompleter, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout
from src.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from src.core.library import Entry, Library, Tag
from src.core.library.alchemy.enums import FilterState
from src.core.library.alchemy.fields import TagBoxField
from src.qt.flowlayout import FlowLayout
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.modals.tag_search import TagSearchPanel
from src.qt.widgets.fields import FieldWidget
from src.qt.widgets.panel import PanelModal
from src.qt.widgets.tag import TagWidget

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class TagCompleter(QCompleter):
    def __init__(self, parent: QObject, lib: Library):
        super().__init__(parent)
        self.lib = lib
        self.update(set())

    def update(self, exclude: set[str]):
        tags = {tag.name for tag in self.lib.tags}
        tags -= exclude
        model = QStringListModel(list(tags), self)
        self.first_choice = model.stringList()[0]
        self.setModel(model)


class TagBoxWidget(FieldWidget):
    updated = Signal()
    error_occurred = Signal(Exception)

    def __init__(
        self,
        field: TagBoxField,
        title: str,
        driver: "QtDriver",
    ) -> None:
        super().__init__(title)

        assert isinstance(field, TagBoxField), f"field is {type(field)}"

        self.field = field
        self.driver = (
            driver  # Used for creating tag click callbacks that search entries for that tag.
        )
        self.setObjectName("tagBox")
        self.base_layout = QVBoxLayout()
        self.setLayout(self.base_layout)

        self.tags_layout = FlowLayout()
        self.base_layout.addLayout(self.tags_layout)
        self.tags_layout.enable_grid_optimizations(value=False)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)

        self.add_layout = QHBoxLayout()
        self.base_layout.addLayout(self.add_layout)

        self.tag_entry = QLineEdit()
        self.add_layout.addWidget(self.tag_entry)

        self.tag_completer = TagCompleter(self.tag_entry, self.driver.lib)
        self.tag_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.tag_completer.setWidget(self.tag_entry)

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
        self.add_layout.addWidget(self.add_button)

        tsp = TagSearchPanel(self.driver.lib)
        tsp.tag_chosen.connect(
            lambda x: (
                self.add_tag_callback(x),
                self.tag_entry.clear(),
            )
        )
        self.add_modal = PanelModal(tsp, title, "Add Tags")

        self.add_button.clicked.connect(
            lambda: (self.add_modal.show(), tsp.update_tags(tsp.search_field.text()))
        )
        self.tag_entry.textChanged.connect(
            lambda text: (
                tsp.search_field.setText(text),
                self.tag_completer.setCompletionPrefix(text),
                self.tag_completer.complete(),
            )
        )
        self.tag_entry.returnPressed.connect(
            lambda: self.tag_completer.activated.emit(
                self.tag_completer.first_choice
                if (self.tag_completer.first_choice and self.tag_entry.text())
                else self.tag_entry.text()
            )
            if not self.tag_completer.popup().selectedIndexes()
            else ()
        )
        self.tag_completer.activated.connect(
            lambda selected: (
                tsp.update_tags(selected),
                self.tag_entry.clear() if tsp.on_return(selected) else (),
            )
        )

        self.set_tags(field.tags)

    def set_field(self, field: TagBoxField):
        self.field = field

    def set_tags(self, tags: typing.Iterable[Tag]):
        self.tag_completer.update({tag.name for tag in tags})
        while self.tags_layout.itemAt(0):
            self.tags_layout.takeAt(0).widget().deleteLater()

        for tag in tags:
            tag_widget = TagWidget(tag, has_edit=True, has_remove=True)
            tag_widget.on_click.connect(
                lambda tag_id=tag.id: (
                    self.driver.main_window.searchField.setText(f"tag_id:{tag_id}"),
                    self.driver.filter_items(FilterState(tag_id=tag_id)),
                )
            )

            tag_widget.on_remove.connect(
                lambda tag_id=tag.id: (
                    self.remove_tag(tag_id),
                    self.driver.preview_panel.update_widgets(),
                )
            )
            tag_widget.on_edit.connect(lambda t=tag: self.edit_tag(t))
            self.tags_layout.addWidget(tag_widget)

    def edit_tag(self, tag: Tag):
        assert isinstance(tag, Tag), f"tag is {type(tag)}"
        build_tag_panel = BuildTagPanel(self.driver.lib, tag=tag)

        self.edit_modal = PanelModal(
            build_tag_panel,
            tag.name,  # TODO - display name including subtags
            "Edit Tag",
            done_callback=self.driver.preview_panel.update_widgets,
            has_save=True,
        )
        # TODO - this was update_tag()
        self.edit_modal.saved.connect(
            lambda: self.driver.lib.update_tag(
                build_tag_panel.build_tag(),
                subtag_ids=build_tag_panel.subtags,
            )
        )
        self.edit_modal.show()

    def add_tag_callback(self, tag_id: int):
        logger.info("add_tag_callback", tag_id=tag_id, selected=self.driver.selected)

        tag = self.driver.lib.get_tag(tag_id=tag_id)
        for idx in self.driver.selected:
            entry: Entry = self.driver.frame_content[idx]

            if not self.driver.lib.add_field_tag(entry, tag, self.field.type_key):
                # TODO - add some visible error
                self.error_occurred.emit(Exception("Failed to add tag"))

        self.updated.emit()

        if tag_id in (TAG_FAVORITE, TAG_ARCHIVED):
            self.driver.update_badges()

    def edit_tag_callback(self, tag: Tag):
        self.driver.lib.update_tag(tag)

    def remove_tag(self, tag_id: int):
        logger.info(
            "remove_tag",
            selected=self.driver.selected,
            field_type=self.field.type,
        )

        for grid_idx in self.driver.selected:
            entry = self.driver.frame_content[grid_idx]
            self.driver.lib.remove_field_tag(entry, tag_id, self.field.type_key)

            self.updated.emit()

        if tag_id in (TAG_FAVORITE, TAG_ARCHIVED):
            self.driver.update_badges()
