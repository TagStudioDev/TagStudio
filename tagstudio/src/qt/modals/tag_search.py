# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math

import structlog
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QFrame,
)

from src.core.library import Library
from src.core.library.alchemy.enums import FilterState
from src.core.palette import ColorType, get_tag_color
from src.qt.widgets.panel import PanelWidget
from src.qt.widgets.tag import TagWidget

ERROR = f"[ERROR]"
WARNING = f"[WARNING]"
INFO = f"[INFO]"

logger = structlog.get_logger(__name__)


class TagSearchPanel(PanelWidget):
    tag_chosen = Signal(int)

    def __init__(self, library: Library):
        super().__init__()
        self.lib = library
        # self.callback = callback
        self.first_tag_id = None
        self.tag_limit = 100
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

    def on_return(self, text: str):
        if text and self.first_tag_id is not None:
            # callback(self.first_tag_id)
            self.tag_chosen.emit(self.first_tag_id)
            self.search_field.setText("")
            self.update_tags()
        else:
            self.search_field.setFocus()
            self.parentWidget().hide()

    def update_tags(self, name: str = None):
        while self.scroll_layout.count():
            self.scroll_layout.takeAt(0).widget().deleteLater()

        found_tags = self.lib.search_tags(
            FilterState(
                name=name,
                page_size=self.tag_limit,
            )
        )

        for tag in found_tags:
            c = QWidget()
            l = QHBoxLayout(c)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(3)
            tw = TagWidget(tag, False, False)
            ab = QPushButton()
            ab.setMinimumSize(23, 23)
            ab.setMaximumSize(23, 23)
            ab.setText("+")
            ab.setStyleSheet(
                f"QPushButton{{"
                f"background: {get_tag_color(ColorType.PRIMARY, tag.color)};"
                f"color: {get_tag_color(ColorType.TEXT, tag.color)};"
                f"font-weight: 600;"
                f"border-color:{get_tag_color(ColorType.BORDER, tag.color)};"
                f"border-radius: 6px;"
                f"border-style:solid;"
                f"border-width: {math.ceil(self.devicePixelRatio())}px;"
                f"padding-bottom: 5px;"
                f"font-size: 20px;"
                f"}}"
                f"QPushButton::hover"
                f"{{"
                f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, tag.color)};"
                f"color: {get_tag_color(ColorType.DARK_ACCENT, tag.color)};"
                f"background: {get_tag_color(ColorType.LIGHT_ACCENT, tag.color)};"
                f"}}"
            )

            ab.clicked.connect(lambda checked=False, x=tag.id: self.tag_chosen.emit(x))

            l.addWidget(tw)
            l.addWidget(ab)
            self.scroll_layout.addWidget(c)

        self.search_field.setFocus()
