# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import math

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
from src.core.palette import ColorType, get_tag_color
from src.qt.widgets.panel import PanelWidget
from src.qt.widgets.tag import TagWidget


ERROR = "[ERROR]"
WARNING = "[WARNING]"
INFO = "[INFO]"

logging.basicConfig(format="%(message)s", level=logging.INFO)


class TagSearchPanel(PanelWidget):
    tag_chosen = Signal(int)

    def __init__(self, library):
        super().__init__()
        self.lib: Library = library
        self.first_tag_id = None
        self.tag_limit = 100
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

        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_area.setWidget(self.scroll_contents)

        self.root_layout.addWidget(self.search_field)
        self.root_layout.addWidget(self.scroll_area)
        self.update_tags("")

    def on_return(self, text: str):
        if text and self.first_tag_id is not None:
            self.tag_chosen.emit(self.first_tag_id)
            self.search_field.setText("")
            self.update_tags()
        else:
            self.search_field.setFocus()
            self.parentWidget().hide()

    def update_tags(self, query: str = ""):
        while self.scroll_layout.count():
            self.scroll_layout.takeAt(0).widget().deleteLater()

        found_tags = self.lib.search_tags(query, include_cluster=True)[: self.tag_limit]
        self.first_tag_id = found_tags[0] if found_tags else None

        for tag_id in found_tags:
            c = QWidget()
            l = QHBoxLayout(c)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(3)
            tw = TagWidget(self.lib, self.lib.get_tag(tag_id), False, False)
            ab = QPushButton()
            ab.setMinimumSize(23, 23)
            ab.setMaximumSize(23, 23)
            ab.setText("+")
            ab.setStyleSheet(
                f"""QPushButton{{
                background: {get_tag_color(ColorType.PRIMARY, self.lib.get_tag(tag_id).color)};
                color: {get_tag_color(ColorType.TEXT, self.lib.get_tag(tag_id).color)};
                font-weight: 600;
                border-color:{get_tag_color(ColorType.BORDER, self.lib.get_tag(tag_id).color)};
                border-radius: 6px;
                border-style:solid;
                border-width: {math.ceil(1*self.devicePixelRatio())}px;
                padding-bottom: 5px;
                }}
                QPushButton::hover
                {{
                border-color:{get_tag_color(ColorType.LIGHT_ACCENT, self.lib.get_tag(tag_id).color)};
                color: {get_tag_color(ColorType.DARK_ACCENT, self.lib.get_tag(tag_id).color)};
                background: {get_tag_color(ColorType.LIGHT_ACCENT, self.lib.get_tag(tag_id).color)};
                }}
                """
            )

            ab.clicked.connect(lambda checked=False, x=tag_id: self.tag_chosen.emit(x))

            l.addWidget(tw)
            l.addWidget(ab)
            self.scroll_layout.addWidget(c)

        self.search_field.setFocus()
