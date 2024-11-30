# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math

import structlog
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library
from src.core.library.alchemy.enums import FilterState
from src.core.palette import ColorType, get_tag_color
from src.qt.widgets.panel import PanelWidget
from src.qt.widgets.tag import TagWidget

logger = structlog.get_logger(__name__)


class TagSearchPanel(PanelWidget):
    tag_chosen = Signal(int)

    def __init__(self, library: Library, exclude: list[int] | None = None):
        super().__init__()
        self.lib = library
        self.exclude = exclude
        self.first_tag_id = None
        self.tag_limit = 100
        self.setMinimumSize(300, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        self.search_field = QLineEdit()
        self.search_field.setObjectName("searchField")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field.setPlaceholderText("Search Tags")
        self.search_field.textEdited.connect(lambda: self.update_tags(self.search_field.text()))
        self.search_field.returnPressed.connect(
            lambda checked=False: self.on_return(self.search_field.text())
        )

        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.scroll_contents)

        self.root_layout.addWidget(self.search_field)
        self.root_layout.addWidget(self.scroll_area)
        self.update_tags()

    def on_return(self, text: str):
        if text and self.first_tag_id is not None:
            # callback(self.first_tag_id)
            self.tag_chosen.emit(self.first_tag_id)
            self.search_field.setText("")
            self.update_tags()
        else:
            self.search_field.setFocus()
            self.parentWidget().hide()

    def update_tags(self, name: str | None = None):
        while self.scroll_layout.count():
            self.scroll_layout.takeAt(0).widget().deleteLater()

        found_tags = self.lib.search_tags(
            FilterState(
                path=name,
                page_size=self.tag_limit,
            )
        )

        for tag in found_tags:
            if self.exclude is not None and tag.id in self.exclude:
                continue
            c = QWidget()
            layout = QHBoxLayout(c)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(3)
            tw = TagWidget(tag, has_edit=False, has_remove=False)
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

            layout.addWidget(tw)
            layout.addWidget(ab)
            self.scroll_layout.addWidget(c)

        self.search_field.setFocus()
