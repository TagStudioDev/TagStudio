# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math

import src.qt.modals.build_tag as bt
import structlog
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from src.core.constants import RESERVED_TAG_END, RESERVED_TAG_START
from src.core.library import Library, Tag
from src.core.library.alchemy.enums import TagColor
from src.core.palette import ColorType, get_tag_color
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import TagWidget

logger = structlog.get_logger(__name__)


class TagSearchPanel(PanelWidget):
    tag_chosen = Signal(int)
    lib: Library
    is_initialized: bool = False
    first_tag_id: int = None
    is_tag_chooser: bool
    exclude: list[int]

    def __init__(self, library: Library, exclude: list[int] = None, is_tag_chooser: bool = True):
        super().__init__()
        self.lib = library
        self.exclude = exclude or []

        self.is_tag_chooser = is_tag_chooser

        self.setMinimumSize(300, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        self.search_field = QLineEdit()
        self.search_field.setObjectName("searchField")
        self.search_field.setMinimumSize(QSize(0, 32))
        Translations.translate_with_setter(self.search_field.setPlaceholderText, "home.search_tags")
        self.search_field.textEdited.connect(lambda: self.update_tags(self.search_field.text()))
        self.search_field.returnPressed.connect(lambda: self.on_return(self.search_field.text()))

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

    def __build_row_item_widget(self, tag: Tag):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)

        has_remove_button = False
        if not self.is_tag_chooser:
            has_remove_button = tag.id not in range(RESERVED_TAG_START, RESERVED_TAG_END)

        tag_widget = TagWidget(
            tag,
            has_edit=True,
            has_remove=has_remove_button,
        )

        tag_widget.on_edit.connect(lambda t=tag: self.edit_tag(t))
        tag_widget.on_remove.connect(lambda t=tag: self.remove_tag(t))
        row.addWidget(tag_widget)

        if self.is_tag_chooser:
            add_button = QPushButton()
            add_button.setMinimumSize(23, 23)
            add_button.setMaximumSize(23, 23)
            add_button.setText("+")
            add_button.setStyleSheet(
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
            tag_id = tag.id
            add_button.clicked.connect(lambda: self.tag_chosen.emit(tag_id))
            row.addWidget(add_button)
        return container

    def construct_tag_button(self, query: str | None):
        """Constructs a Create Tag Button."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)

        create_button = QPushButton(self)
        Translations.translate_qobject(create_button, "tag.create_quick", query=query)
        create_button.setFlat(True)

        inner_layout = QHBoxLayout()
        inner_layout.setObjectName("innerLayout")
        inner_layout.setContentsMargins(2, 2, 2, 2)
        create_button.setLayout(inner_layout)
        create_button.setMinimumSize(math.ceil(22 * 1.5), 22)

        create_button.setStyleSheet(
            f"QPushButton{{"
            f"background: {get_tag_color(ColorType.PRIMARY, TagColor.DEFAULT)};"
            f"color: {get_tag_color(ColorType.TEXT, TagColor.DEFAULT)};"
            f"font-weight: 600;"
            f"border-color:{get_tag_color(ColorType.BORDER, TagColor.DEFAULT)};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: {math.ceil(self.devicePixelRatio())}px;"
            f"padding-right: 4px;"
            f"padding-bottom: 1px;"
            f"padding-left: 4px;"
            f"font-size: 13px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, TagColor.DEFAULT)};"
            f"}}"
        )

        create_button.clicked.connect(lambda: self.create_and_add_tag(query))
        row.addWidget(create_button)

        return container

    def create_and_add_tag(self, name: str):
        """Opens "Create Tag" panel to create and add a new tag with given name."""
        logger.info("Quick Create Tag", name=name)

        def on_tag_modal_saved():
            """Callback for actions to perform when a new tag is confirmed created."""
            tag: Tag = self.build_tag_modal.build_tag()
            self.lib.add_tag(tag)
            self.add_tag_modal.hide()

            self.tag_chosen.emit(tag.id)
            self.update_tags()

        self.build_tag_modal: bt.BuildTagPanel = bt.BuildTagPanel(self.lib)
        self.add_tag_modal: PanelModal = PanelModal(
            self.build_tag_modal, "New Tag", "Add Tag", has_save=True
        )
        self.build_tag_modal.name_field.setText(name)
        self.add_tag_modal.saved.connect(on_tag_modal_saved)
        self.add_tag_modal.save_button.setFocus()
        self.add_tag_modal.show()

    def update_tags(self, query: str | None = None):
        logger.info("[Tag Search Super Class] Updating Tags")

        # TODO: Look at recycling rather than deleting and re-initializing
        while self.scroll_layout.count():
            self.scroll_layout.takeAt(0).widget().deleteLater()

        tag_results = self.lib.search_tags(name=query)
        if len(tag_results) > 0:
            self.first_tag_id = tag_results[0].id
        else:
            self.first_tag_id = None

        for tag in tag_results:
            if tag.id not in self.exclude:
                self.scroll_layout.addWidget(self.__build_row_item_widget(tag))

        # If query doesnt exist add create button
        if len(tag_results) == 0:
            c = self.construct_tag_button(query)
            self.scroll_layout.addWidget(c)

        self.search_field.setFocus()

    def on_return(self, text: str):
        if text and self.first_tag_id is not None:
            if self.is_tag_chooser:
                self.tag_chosen.emit(self.first_tag_id)
            self.search_field.setText("")
            self.update_tags()
        else:
            self.search_field.setFocus()
            self.parentWidget().hide()

    def showEvent(self, event: QShowEvent) -> None:  # noqa N802
        if not self.is_initialized:
            self.update_tags()
            self.is_initialized = True
        return super().showEvent(event)

    def remove_tag(self, tag: Tag):
        pass

    def edit_tag(self, tag: Tag):
        def callback(btp: bt.BuildTagPanel):
            self.lib.update_tag(
                btp.build_tag(), set(btp.parent_ids), set(btp.alias_names), set(btp.alias_ids)
            )
            self.update_tags(self.search_field.text())

        build_tag_panel = bt.BuildTagPanel(self.lib, tag=tag)

        self.edit_modal = PanelModal(
            build_tag_panel,
            tag.name,
            done_callback=(self.update_tags(self.search_field.text())),
            has_save=True,
        )
        Translations.translate_with_setter(self.edit_modal.setWindowTitle, "tag.edit")

        self.edit_modal.saved.connect(lambda: callback(build_tag_panel))
        self.edit_modal.show()
