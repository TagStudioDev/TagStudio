# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import math
import src.qt.modals.build_tag as bt
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
from src.core.constants import TAG_COLORS
from src.core.library import Library
from src.core.palette import ColorType, get_tag_color
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import TagWidget

ERROR = "[ERROR]"
WARNING = "[WARNING]"
INFO = "[INFO]"

logging.basicConfig(format="%(message)s", level=logging.INFO)


class TagSearchPanel(PanelWidget):
    tag_created = Signal(int)

    def __init__(self, library: "Library"):
        super().__init__()
        self.lib: Library = library
        self.first_tag_id: int | None = None
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
            # callback(self.first_tag_id)
            self.tag_created.emit(self.first_tag_id)
            self.search_field.setText("")
            self.update_tags()
        elif text:
            self.create_and_add_tag(text)
            self.parentWidget().hide()
        else:
            self.parentWidget().hide()

    def update_tags(self, query: str = ""):
        while self.scroll_layout.count():
            self.scroll_layout.takeAt(0).widget().deleteLater()

        found_tags = self.lib.search_tags(query, include_cluster=True)[: self.tag_limit]
        self.first_tag_id = found_tags[0] if found_tags else None

        if query:
            # sort tags by whether the tag's name is the text that's matching the search, alphabetically, and then by color
            sorted_tags = sorted(
                found_tags,
                key=lambda tag_id: (
                    not self.lib.get_tag(tag_id).name.lower().startswith(query.lower()),
                    self.lib.get_tag(tag_id).display_name(self.lib),
                    TAG_COLORS.index(self.lib.get_tag(tag_id).color.lower()),
                ),
            )
        else:
            # sort tags by color and then alphabetically
            sorted_tags = sorted(
                found_tags,
                key=lambda tag_id: (
                    TAG_COLORS.index(self.lib.get_tag(tag_id).color.lower()),
                    self.lib.get_tag(tag_id).display_name(self.lib),
                ),
            )

        for tag_id in sorted_tags:
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
                f"QPushButton{{"
                f"background: {get_tag_color(ColorType.PRIMARY, self.lib.get_tag(tag_id).color)};"
                # f'background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {get_tag_color(ColorType.PRIMARY, tag.color)}, stop:1.0 {get_tag_color(ColorType.BORDER, tag.color)});'
                # f"border-color:{get_tag_color(ColorType.PRIMARY, tag.color)};"
                f"color: {get_tag_color(ColorType.TEXT, self.lib.get_tag(tag_id).color)};"
                f"font-weight: 600;"
                f"border-color:{get_tag_color(ColorType.BORDER, self.lib.get_tag(tag_id).color)};"
                f"border-radius: 6px;"
                f"border-style:solid;"
                f"border-width: {math.ceil(1*self.devicePixelRatio())}px;"
                f"padding-bottom: 5px;"
                f"font-size: 20px;"
                f"}}"
                f"QPushButton::hover"
                f"{{"
                f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, self.lib.get_tag(tag_id).color)};"
                f"color: {get_tag_color(ColorType.DARK_ACCENT, self.lib.get_tag(tag_id).color)};"
                f"background: {get_tag_color(ColorType.LIGHT_ACCENT, self.lib.get_tag(tag_id).color)};"
                f"}}"
            )

            ab.clicked.connect(lambda checked=False, x=tag_id: self.tag_created.emit(x))

            l.addWidget(tw)
            l.addWidget(ab)
            self.scroll_layout.addWidget(c)

        # Add a create tag button if a query is entered
        if query:
            c = self.create_tag_button(query)
            self.scroll_layout.addWidget(c)

        self.search_field.setFocus()

    def create_tag_button(self, name: str) -> QWidget:
        """Construct a "Create Tag" button.

        Args:
            name (str): The name of the tag to give.
        """
        c = QWidget()
        l = QHBoxLayout(c)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(3)

        create_and_add_button = QPushButton(self)
        create_and_add_button.setFlat(True)
        create_and_add_button.setText(
            f"Create && Add \"{name.replace("&", "&&")}\" Tag"
        )

        inner_layout = QHBoxLayout()
        inner_layout.setObjectName("innerLayout")
        inner_layout.setContentsMargins(2, 2, 2, 2)
        create_and_add_button.setLayout(inner_layout)
        create_and_add_button.setMinimumSize(math.ceil(22 * 1.5), 22)

        create_and_add_button.setStyleSheet(
            f"QPushButton{{"
            f"background: {get_tag_color(ColorType.PRIMARY, "dark gray")};"
            f"color: {get_tag_color(ColorType.TEXT, "dark gray")};"
            f"font-weight: 600;"
            f"border-color:{get_tag_color(ColorType.BORDER, "dark gray")};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: {math.ceil(self.devicePixelRatio())}px;"
            f"padding-right: 4px;"
            f"padding-bottom: 1px;"
            f"padding-left: 4px;"
            f"font-size: 13px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, "dark gray")};"
            f"}}"
        )

        create_and_add_button.clicked.connect(
            lambda x=name: self.create_and_add_tag(name)
        )
        l.addWidget(create_and_add_button)

        return c

    def create_and_add_tag(self, name: str):
        """Open "Add Tag" panel to create and add a new tag with the given name.

        Args:
            name (str): The name of the tag to give.
        """
        self.add_tag_modal = PanelModal(
            bt.BuildTagPanel(self.lib, tag_name=name),
            "New Tag",
            "Add Tag",
            has_save=True,
        )
        self.add_tag_modal.saved.connect(lambda n=name: self.on_tag_modal_saved(n))
        self.add_tag_modal.save_button.setFocus()
        self.add_tag_modal.show()

    def on_tag_modal_saved(self, name):
        """Callback for actions to perform when a new "Create & Add" tag is confirmed.
        Args:
            name (str): The name of the tag to give.
        """
        panel: bt.BuildTagPanel = self.add_tag_modal.widget
        self.tag_created.emit(self.lib.add_tag_to_library(panel.build_tag()))
        self.add_tag_modal.hide()
        self.update_tags(name)

    def showEvent(self, event):
        # Clear search field and focus when showing modal
        self.search_field.setText("")
        self.search_field.setFocus()
