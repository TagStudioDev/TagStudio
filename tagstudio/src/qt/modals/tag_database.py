# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QFrame,
)

from src.core.library import Library
from src.qt.widgets.panel import PanelWidget, PanelModal
from src.qt.widgets.tag import TagWidget
from src.qt.modals.build_tag import BuildTagPanel


class TagDatabasePanel(PanelWidget):
    tag_chosen = Signal(int)

    def __init__(self, library):
        super().__init__()
        self.lib: Library = library
        # self.callback = callback
        self.first_tag_id = -1
        self.tag_limit = 30
        # self.selected_tag: int = 0

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

        first_id_set = False
        for tag_id in tags:
            if not first_id_set:
                self.first_tag_id = tag_id
                first_id_set = True
            container = QWidget()
            row = QHBoxLayout(container)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(3)
            tw = TagWidget(self.lib, self.lib.get_tag(tag_id), True, False)
            tw.on_edit.connect(
                lambda checked=False, t=self.lib.get_tag(tag_id): (self.edit_tag(t.id))
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
