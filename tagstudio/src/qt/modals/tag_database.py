# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from src.core.constants import TAG_COLORS
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import TagWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.core.library import Library, Tag
    from src.qt.ts_qt import QtDriver


class TagDatabasePanel(PanelWidget):
    tag_chosen = Signal(int)

    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib: Library = library
        self.driver: QtDriver = driver
        self.first_tag_id = -1
        self.tag_limit = 30

        self.setMinimumSize(300, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        self.search_field = QLineEdit()
        self.search_field.setObjectName("searchField")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field.setPlaceholderText("Search Tags")
        self.search_field.textEdited.connect(
            lambda x=self.search_field.text(): self.update_tags(x)
        )
        self.search_field.returnPressed.connect(
            lambda checked=False: self.on_return(self.search_field.text())
        )

        # self.content_container = QWidget()
        # self.content_layout = QHBoxLayout(self.content_container)

        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        # self.scroll_area.setStyleSheet('background: #000000;')
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        # self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        # sa.setMaximumWidth(self.preview_size[0])
        self.scroll_area.setWidget(self.scroll_contents)

        # self.add_button = QPushButton()
        # self.root_layout.addWidget(self.add_button)
        # self.add_button.setText('Add Tag')
        # # self.done_button.clicked.connect(lambda checked=False, x=1101: (callback(x), self.hide()))
        # self.add_button.clicked.connect(lambda checked=False, x=1101: callback(x))
        # # self.setLayout(self.root_layout)

        self.root_layout.addWidget(self.search_field)
        self.root_layout.addWidget(self.scroll_area)
        self.update_tags("")

    # def reset(self):
    # 	self.search_field.setText('')
    # 	self.update_tags('')
    # 	self.search_field.setFocus()

    def on_return(self, text: str):
        if text and self.first_tag_id >= 0:
            # callback(self.first_tag_id)
            self.search_field.setText("")
            self.update_tags("")
        else:
            self.search_field.setFocus()
            self.parentWidget().hide()

    def update_tags(self, query: str):
        # TODO: Look at recycling rather than deleting and reinitializing
        while self.scroll_layout.itemAt(0):
            self.scroll_layout.takeAt(0).widget().deleteLater()

        # If there is a query, get a list of tag_ids that match, otherwise return all
        if query:
            tags = self.lib.search_tags(query, include_cluster=True)[
                : self.tag_limit - 1
            ]
        else:
            # Get tag ids to keep this behaviorally identical
            tags = [t.id for t in self.lib.tags]

        if query:
            # sort tags by whether the tag's name is the text that's matching the search, alphabetically, and then by color
            sorted_tags = sorted(
                tags,
                key=lambda tag_id: (
                    not self.lib.get_tag(tag_id).name.lower().startswith(query.lower()),
                    self.lib.get_tag(tag_id).display_name(self.lib),
                    TAG_COLORS.index(self.lib.get_tag(tag_id).color.lower()),
                ),
            )
        else:
            # sort tags by color and then alphabetically
            sorted_tags = sorted(
                tags,
                key=lambda tag_id: (
                    TAG_COLORS.index(self.lib.get_tag(tag_id).color.lower()),
                    self.lib.get_tag(tag_id).display_name(self.lib),
                ),
            )

        first_id_set = False
        for tag_id in sorted_tags:
            if not first_id_set:
                self.first_tag_id = tag_id
                first_id_set = True
            container = QWidget()
            row = QHBoxLayout(container)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(3)
            tag: Tag = self.lib.get_tag(tag_id)
            tw = TagWidget(self.lib, tag, True, False)
            tw.on_edit.connect(lambda checked=False, t=tag: (self.edit_tag(t.id)))
            tw.on_click.connect(
                lambda checked=False, q=f"tag_id: {tag_id}": (
                    self.driver.main_window.searchField.setText(q),
                    self.driver.filter_items(q),
                )
            )
            row.addWidget(tw)
            self.scroll_layout.addWidget(container)

        self.search_field.setFocus()

    def edit_tag(self, tag_id: int):
        btp = BuildTagPanel(self.lib, tag_id)
        # btp.on_edit.connect(lambda x: self.edit_tag_callback(x))
        self.edit_modal = PanelModal(
            btp,
            self.lib.get_tag(tag_id).display_name(self.lib),
            "Edit Tag",
            done_callback=(self.update_tags(self.search_field.text())),
            has_save=True,
        )
        # self.edit_modal.widget.update_display_name.connect(lambda t: self.edit_modal.title_widget.setText(t))
        # TODO Check Warning: Expected type 'BuildTagPanel', got 'PanelWidget' instead
        self.edit_modal.saved.connect(lambda: self.edit_tag_callback(btp))
        self.edit_modal.show()

    def edit_tag_callback(self, btp: BuildTagPanel):
        self.lib.update_tag(btp.build_tag())
        self.update_tags(self.search_field.text())

    # def enterEvent(self, event: QEnterEvent) -> None:
    # 	self.search_field.setFocus()
    # 	return super().enterEvent(event)
    # 	self.focusOutEvent
