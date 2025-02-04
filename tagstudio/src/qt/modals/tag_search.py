# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import contextlib
import typing
from warnings import catch_warnings

import src.qt.modals.build_tag as build_tag
import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QFrame,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from src.core.constants import RESERVED_TAG_END, RESERVED_TAG_START
from src.core.library import Library, Tag
from src.core.library.alchemy.enums import FilterState, TagColorEnum
from src.core.palette import ColorType, get_tag_color
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import (
    TagWidget,
)

logger = structlog.get_logger(__name__)

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.modals.build_tag import BuildTagPanel


class TagSearchPanel(PanelWidget):
    tag_chosen = Signal(int)
    lib: Library
    is_initialized: bool = False
    first_tag_id: int | None = None
    is_tag_chooser: bool
    exclude: list[int]

    TAG_LIMIT = 100

    def __init__(
        self,
        library: Library,
        exclude: list[int] = None,
        is_tag_chooser: bool = True,
    ):
        super().__init__()
        self.lib = library
        self.driver = None
        self.exclude = exclude or []

        self.is_tag_chooser = is_tag_chooser
        self.create_button_in_layout: bool = False

        self.setMinimumSize(300, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        self.search_field = QLineEdit()
        self.search_field.setObjectName("searchField")
        self.search_field.setMinimumSize(QSize(0, 32))
        Translations.translate_with_setter(self.search_field.setPlaceholderText, "home.search_tags")
        self.search_field.textEdited.connect(lambda text: self.update_tags(text))
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

    def set_driver(self, driver):
        """Set the QtDriver for this search panel. Used for main window operations."""
        self.driver = driver

    def build_create_button(self, query: str | None):
        """Constructs a "Create & Add Tag" QPushButton."""
        create_button = QPushButton(self)
        create_button.setFlat(True)

        create_button.setMinimumSize(22, 22)

        create_button.setStyleSheet(
            f"QPushButton{{"
            f"background: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};"
            f"color: {get_tag_color(ColorType.TEXT, TagColorEnum.DEFAULT)};"
            f"font-weight: 600;"
            f"border-color:{get_tag_color(ColorType.BORDER, TagColorEnum.DEFAULT)};"
            f"border-radius: 6px;"
            f"border-style:dashed;"
            f"border-width: 2px;"
            f"padding-right: 4px;"
            f"padding-bottom: 1px;"
            f"padding-left: 4px;"
            f"font-size: 13px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};"
            f"}}"
            f"QPushButton::pressed{{"
            f"background: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};"
            f"color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};"
            f"border-color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};"
            f"}}"
            f"QPushButton::focus{{"
            f"border-color: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};"
            f"outline:none;"
            f"}}"
        )

        return create_button

    def create_and_add_tag(self, name: str):
        """Opens "Create Tag" panel to create and add a new tag with given name."""
        logger.info("Create and Add Tag", name=name)

        def on_tag_modal_saved():
            """Callback for actions to perform when a new tag is confirmed created."""
            tag: Tag = self.build_tag_modal.build_tag()
            self.lib.add_tag(
                tag,
                set(self.build_tag_modal.parent_ids),
                set(self.build_tag_modal.alias_names),
                set(self.build_tag_modal.alias_ids),
            )
            self.add_tag_modal.hide()

            self.tag_chosen.emit(tag.id)
            self.search_field.setText("")
            self.search_field.setFocus()
            self.update_tags()

        self.build_tag_modal: BuildTagPanel = build_tag.BuildTagPanel(self.lib)
        self.add_tag_modal: PanelModal = PanelModal(self.build_tag_modal, has_save=True)
        Translations.translate_with_setter(self.add_tag_modal.setTitle, "tag.new")
        Translations.translate_with_setter(self.add_tag_modal.setWindowTitle, "tag.add")

        self.build_tag_modal.name_field.setText(name)
        self.add_tag_modal.saved.connect(on_tag_modal_saved)
        self.add_tag_modal.show()

    def update_tags(self, query: str | None = None):
        """Update the tag list given a search query."""
        logger.info("[TagSearchPanel] Updating Tags")

        # Remove the "Create & Add" button if one exists
        create_button: QPushButton | None = None
        if self.create_button_in_layout and self.scroll_layout.count():
            create_button = self.scroll_layout.takeAt(self.scroll_layout.count() - 1).widget()  # type: ignore
            create_button.deleteLater()
            self.create_button_in_layout = False

        # Get results for the search query
        query_lower = "" if not query else query.lower()
        tag_results: list[set[Tag]] = self.lib.search_tags(name=query)
        if self.exclude:
            tag_results[0] = {t for t in tag_results[0] if t.id not in self.exclude}
            tag_results[1] = {t for t in tag_results[1] if t.id not in self.exclude}

        # Sort and prioritize the results
        results_0 = list(tag_results[0])
        results_0.sort(key=lambda tag: tag.name.lower())
        results_1 = list(tag_results[1])
        results_1.sort(key=lambda tag: tag.name.lower())
        raw_results = list(results_0 + results_1)[: TagSearchPanel.TAG_LIMIT]
        priority_results: set[Tag] = set()
        all_results: list[Tag] = []

        if query and query.strip():
            for tag in raw_results:
                if tag.name.lower().startswith(query_lower):
                    priority_results.add(tag)

        all_results = sorted(list(priority_results), key=lambda tag: len(tag.name)) + [
            r for r in raw_results if r not in priority_results
        ]

        if all_results:
            self.first_tag_id = None
            self.first_tag_id = all_results[0].id if len(all_results) > 0 else all_results[0].id

        else:
            self.first_tag_id = None

        # Update every tag widget with the new search result data
        for i in range(0, TagSearchPanel.TAG_LIMIT):
            tag = None
            with contextlib.suppress(IndexError):
                tag = all_results[i]
            self.set_tag_widget(tag=tag, index=i)

        # Add back the "Create & Add" button
        if query and query.strip():
            cb: QPushButton = self.build_create_button(query)
            with catch_warnings(record=True):
                cb.clicked.disconnect()
            cb.clicked.connect(lambda: self.create_and_add_tag(query or ""))
            Translations.translate_qobject(cb, "tag.create_add", query=query)
            self.scroll_layout.addWidget(cb)
            self.create_button_in_layout = True

    def set_tag_widget(self, tag: Tag | None, index: int):
        """Set the tag of a tag widget at a specific index."""
        # Create any new tag widgets needed up to the given index
        if self.scroll_layout.count() <= index:
            while self.scroll_layout.count() <= index:
                new_tw = TagWidget(tag=None, has_edit=True, has_remove=True, library=self.lib)
                new_tw.setHidden(True)
                self.scroll_layout.addWidget(new_tw)

        # Assign the tag to the widget at the given index.
        tag_widget: TagWidget = self.scroll_layout.itemAt(index).widget()  # type: ignore
        tag_widget.set_tag(tag)

        # Set tag widget viability and potentially return early
        tag_widget.setHidden(bool(not tag))
        if not tag:
            return

        # Configure any other aspects of the tag widget
        has_remove_button = False
        if not self.is_tag_chooser:
            has_remove_button = tag.id not in range(RESERVED_TAG_START, RESERVED_TAG_END)
        tag_widget.has_remove = has_remove_button

        with catch_warnings(record=True):
            tag_widget.on_edit.disconnect()
            tag_widget.on_remove.disconnect()
            tag_widget.bg_button.clicked.disconnect()

        tag_id = tag.id
        tag_widget.on_edit.connect(lambda t=tag: self.edit_tag(t))
        tag_widget.on_remove.connect(lambda t=tag: self.remove_tag(t))
        tag_widget.bg_button.clicked.connect(lambda: self.tag_chosen.emit(tag_id))

        if self.driver:
            tag_widget.search_for_tag_action.triggered.connect(
                lambda checked=False, tag_id=tag.id: (
                    self.driver.main_window.searchField.setText(f"tag_id:{tag_id}"),
                    self.driver.filter_items(FilterState.from_tag_id(tag_id)),
                )
            )
            tag_widget.search_for_tag_action.setEnabled(True)
        else:
            tag_widget.search_for_tag_action.setEnabled(False)

    def on_return(self, text: str):
        if text:
            if self.first_tag_id is not None:
                if self.is_tag_chooser:
                    self.tag_chosen.emit(self.first_tag_id)
                self.search_field.setText("")
                self.update_tags()
            else:
                self.create_and_add_tag(text)
        else:
            self.search_field.setFocus()
            self.parentWidget().hide()

    def showEvent(self, event: QShowEvent) -> None:  # noqa N802
        self.update_tags()
        self.search_field.setText("")
        self.search_field.setFocus()
        return super().showEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        # When Escape is pressed, focus back on the search box.
        # If focus is already on the search box, close the modal.
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.search_field.hasFocus():
                self.parentWidget().hide()
            else:
                self.search_field.setFocus()
                self.search_field.selectAll()
        return super().keyPressEvent(event)

    def remove_tag(self, tag: Tag):
        pass

    def edit_tag(self, tag: Tag):
        def callback(btp: build_tag.BuildTagPanel):
            self.lib.update_tag(
                btp.build_tag(), set(btp.parent_ids), set(btp.alias_names), set(btp.alias_ids)
            )
            self.update_tags(self.search_field.text())

        build_tag_panel = build_tag.BuildTagPanel(self.lib, tag=tag)

        self.edit_modal = PanelModal(
            build_tag_panel,
            self.lib.tag_display_name(tag.id),
            done_callback=(self.update_tags(self.search_field.text())),
            has_save=True,
        )
        Translations.translate_with_setter(self.edit_modal.setWindowTitle, "tag.edit")

        self.edit_modal.saved.connect(lambda: callback(build_tag_panel))
        self.edit_modal.show()
