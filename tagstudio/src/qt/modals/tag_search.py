# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math

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
from src.core.library.alchemy.enums import TagColorEnum
from src.core.library.alchemy.models import TagColor
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
                f"background: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};"
                f"color: {get_tag_color(ColorType.TEXT, TagColorEnum.DEFAULT)};"
                f"font-weight: 600;"
                f"border-color:{get_tag_color(ColorType.BORDER, TagColorEnum.DEFAULT)};"
                f"border-radius: 6px;"
                f"border-style:solid;"
                f"border-width: {math.ceil(self.devicePixelRatio())}px;"
                f"padding-bottom: 5px;"
                f"font-size: 20px;"
                f"}}"
                f"QPushButton::hover"
                f"{{"
                f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};"
                f"color: {get_tag_color(ColorType.DARK_ACCENT, TagColorEnum.DEFAULT)};"
                f"background: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};"
                f"}}"
            )
            tag_id = tag.id
            add_button.clicked.connect(lambda: self.tag_chosen.emit(tag_id))
            row.addWidget(add_button)
        return container

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
        # only import here because of circular imports
        from src.qt.modals.build_tag import BuildTagPanel

        def callback(btp: BuildTagPanel):
            self.lib.update_tag(
                btp.build_tag(), set(btp.parent_ids), set(btp.alias_names), set(btp.alias_ids)
            )
            self.update_tags(self.search_field.text())

        build_tag_panel = BuildTagPanel(self.lib, tag=tag)

        self.edit_modal = PanelModal(
            build_tag_panel,
            tag.name,
            done_callback=(self.update_tags(self.search_field.text())),
            has_save=True,
        )
        Translations.translate_with_setter(self.edit_modal.setWindowTitle, "tag.edit")

        self.edit_modal.saved.connect(lambda: callback(build_tag_panel))
        self.edit_modal.show()
