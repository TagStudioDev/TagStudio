# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QFrame,
    QTextEdit,
    QColorDialog,
)

from src.core.library import Library, Tag
from src.core.constants import DEFAULT_TAG_COLOR
from src.qt.widgets.panel import PanelWidget, PanelModal
from src.qt.widgets.tag import TagWidget
from src.qt.modals.tag_search import TagSearchPanel


ERROR = f"[ERROR]"
WARNING = f"[WARNING]"
INFO = f"[INFO]"

logging.basicConfig(format="%(message)s", level=logging.INFO)


class BuildTagPanel(PanelWidget):
    on_edit = Signal(Tag)

    def __init__(self, library, tag_id: int = -1):
        super().__init__()
        self.lib: Library = library
        # self.callback = callback
        # self.tag_id = tag_id
        self.tag = None
        self.setMinimumSize(300, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Name -----------------------------------------------------------------
        self.name_widget = QWidget()
        self.name_layout = QVBoxLayout(self.name_widget)
        self.name_layout.setStretch(1, 1)
        self.name_layout.setContentsMargins(0, 0, 0, 0)
        self.name_layout.setSpacing(0)
        self.name_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.name_title = QLabel()
        self.name_title.setText("Name")
        self.name_layout.addWidget(self.name_title)
        self.name_field = QLineEdit()
        self.name_layout.addWidget(self.name_field)

        # Shorthand ------------------------------------------------------------
        self.shorthand_widget = QWidget()
        self.shorthand_layout = QVBoxLayout(self.shorthand_widget)
        self.shorthand_layout.setStretch(1, 1)
        self.shorthand_layout.setContentsMargins(0, 0, 0, 0)
        self.shorthand_layout.setSpacing(0)
        self.shorthand_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.shorthand_title = QLabel()
        self.shorthand_title.setText("Shorthand")
        self.shorthand_layout.addWidget(self.shorthand_title)
        self.shorthand_field = QLineEdit()
        self.shorthand_layout.addWidget(self.shorthand_field)

        # Aliases --------------------------------------------------------------
        self.aliases_widget = QWidget()
        self.aliases_layout = QVBoxLayout(self.aliases_widget)
        self.aliases_layout.setStretch(1, 1)
        self.aliases_layout.setContentsMargins(0, 0, 0, 0)
        self.aliases_layout.setSpacing(0)
        self.aliases_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.aliases_title = QLabel()
        self.aliases_title.setText("Aliases")
        self.aliases_layout.addWidget(self.aliases_title)
        self.aliases_field = QTextEdit()
        self.aliases_field.setAcceptRichText(False)
        self.aliases_field.setMinimumHeight(40)
        self.aliases_layout.addWidget(self.aliases_field)

        # Subtags ------------------------------------------------------------
        self.subtags_widget = QWidget()
        self.subtags_layout = QVBoxLayout(self.subtags_widget)
        self.subtags_layout.setStretch(1, 1)
        self.subtags_layout.setContentsMargins(0, 0, 0, 0)
        self.subtags_layout.setSpacing(0)
        self.subtags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.subtags_title = QLabel()
        self.subtags_title.setText("Parent Tags")
        self.subtags_layout.addWidget(self.subtags_title)

        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        # self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.scroll_contents)
        # self.scroll_area.setMinimumHeight(60)

        self.subtags_layout.addWidget(self.scroll_area)

        self.subtags_add_button = QPushButton()
        self.subtags_add_button.setText("+")
        tsp = TagSearchPanel(self.lib)
        tsp.tag_chosen.connect(lambda x: self.add_subtag_callback(x))
        self.add_tag_modal = PanelModal(tsp, "Add Parent Tags", "Add Parent Tags")
        self.subtags_add_button.clicked.connect(self.add_tag_modal.show)
        self.subtags_layout.addWidget(self.subtags_add_button)

        # self.subtags_field = TagBoxWidget()
        # self.subtags_field.setMinimumHeight(60)
        # self.subtags_layout.addWidget(self.subtags_field)

        # Colors ------------------------------------------------------------
        self.selected_color = DEFAULT_TAG_COLOR

        self.color_widget = QWidget()
        self.color_layout = QVBoxLayout(self.color_widget)
        self.color_layout.setStretch(2, 1)
        self.color_layout.setContentsMargins(0, 0, 0, 0)
        self.color_layout.setSpacing(0)
        self.color_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.color_title = QLabel()
        self.color_title.setText("Color")
        self.color_layout.addWidget(self.color_title)
        self.color_add_button = QPushButton("+")
        self.color_add_button.clicked.connect(self.set_color)
        self.color_add_button.setStyleSheet(f"background-color: {self.selected_color}")
        self.color_layout.addWidget(self.color_add_button)

        # Add Widgets to Layout ================================================
        self.root_layout.addWidget(self.name_widget)
        self.root_layout.addWidget(self.shorthand_widget)
        self.root_layout.addWidget(self.aliases_widget)
        self.root_layout.addWidget(self.subtags_widget)
        self.root_layout.addWidget(self.color_widget)
        # self.parent().done.connect(self.update_tag)

        if tag_id >= 0:
            self.tag = self.lib.get_tag(tag_id)
        else:
            self.tag = Tag(-1, "New Tag", "", [], [], "")
        self.set_tag(self.tag)

    def add_subtag_callback(self, tag_id: int):
        logging.info(f"adding {tag_id}")
        # tag = self.lib.get_tag(self.tag_id)
        # TODO: Create a single way to update tags and refresh library data
        # new = self.build_tag()
        self.tag.add_subtag(tag_id)
        # self.tag = new
        # self.lib.update_tag(new)
        self.set_subtags()
        # self.on_edit.emit(self.build_tag())

    def remove_subtag_callback(self, tag_id: int):
        logging.info(f"removing {tag_id}")
        # tag = self.lib.get_tag(self.tag_id)
        # TODO: Create a single way to update tags and refresh library data
        # new = self.build_tag()
        self.tag.remove_subtag(tag_id)
        # self.tag = new
        # self.lib.update_tag(new)
        self.set_subtags()
        # self.on_edit.emit(self.build_tag())

    def set_subtags(self):
        while self.scroll_layout.itemAt(0):
            self.scroll_layout.takeAt(0).widget().deleteLater()
        logging.info(f"Setting {self.tag.subtag_ids}")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(3)
        for tag_id in self.tag.subtag_ids:
            tw = TagWidget(self.lib, self.lib.get_tag(tag_id), False, True)
            tw.on_remove.connect(
                lambda checked=False, t=tag_id: self.remove_subtag_callback(t)
            )
            l.addWidget(tw)
        self.scroll_layout.addWidget(c)

    def set_color(self):
        color = QColorDialog.getColor(initial=self.selected_color)
        if color.isValid():
            self.selected_color = color.name(format=QColor.NameFormat.HexRgb)
            self.color_add_button.setStyleSheet(f"background-color: {self.selected_color}")

    def set_tag(self, tag: Tag):
        # tag = self.lib.get_tag(tag_id)
        self.name_field.setText(tag.name)
        self.shorthand_field.setText(tag.shorthand)
        self.aliases_field.setText("\n".join(tag.aliases))
        self.set_subtags()
        # self.tag_id = tag.id

    def build_tag(self) -> Tag:
        # tag: Tag = self.tag
        # if self.tag_id >= 0:
        # 	tag = self.lib.get_tag(self.tag_id)
        # else:
        # 	tag = Tag(-1, '', '', [], [], '')
        new_tag: Tag = Tag(
            id=self.tag.id,
            name=self.name_field.text(),
            shorthand=self.shorthand_field.text(),
            aliases=self.aliases_field.toPlainText().split("\n"),
            subtags_ids=self.tag.subtag_ids,
            color=self.selected_color,
        )
        logging.info(f"built {new_tag}")
        return new_tag

        # NOTE: The callback and signal do the same thing, I'm currently
        # transitioning from using callbacks to the Qt method of using signals.
        # self.tag_updated.emit(new_tag)
        # self.callback(new_tag)

    # def on_return(self, callback, text:str):
    # 	if text and self.first_tag_id >= 0:
    # 		callback(self.first_tag_id)
    # 		self.search_field.setText('')
    # 		self.update_tags('')
    # 	else:
    # 		self.search_field.setFocus()
    # 		self.parentWidget().hide()
