# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import traceback
import typing
from pathlib import Path
from warnings import catch_warnings

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QVBoxLayout, QWidget
from src.core.library.alchemy.library import Library
from src.core.library.alchemy.models import Entry
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper
from src.qt.modals.add_field import AddFieldModal
from src.qt.modals.tag_search import TagSearchPanel
from src.qt.widgets.panel import PanelModal

# from src.qt.modals.add_tag import AddTagModal
from src.qt.widgets.preview.field_containers import FieldContainers
from src.qt.widgets.preview.file_attributes import FileAttributes
from src.qt.widgets.preview.preview_thumb import PreviewThumb
from src.qt.translations import Translations

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class PreviewPanel(QWidget):
    """The Preview Panel Widget."""

    tags_updated = Signal()

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver: QtDriver = driver
        self.initialized = False
        self.is_open: bool = True

        self.thumb = PreviewThumb(library, driver)
        self.file_attrs = FileAttributes(library, driver)
        self.fields = FieldContainers(library, driver)

        tsp = TagSearchPanel(self.driver.lib)
        # tsp.tag_chosen.connect(lambda x: self.add_tag_callback(x))
        self.add_tag_modal = PanelModal(tsp, "Add Tags", "Add Tags")

        # self.add_tag_modal = AddTagModal(self.lib)
        self.add_field_modal = AddFieldModal(self.lib)

        preview_section = QWidget()
        preview_layout = QVBoxLayout(preview_section)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(6)

        info_section = QWidget()
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(6)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Vertical)
        splitter.setHandleWidth(12)
        # splitter.splitterMoved.connect(
        #     lambda: self.thumb.update_image_size(
        #         (
        #             self.thumb.image_container.size().width(),
        #             self.thumb.image_container.size().height(),
        #         )
        #     )
        # )
        add_buttons_container = QWidget()
        add_buttons_layout = QHBoxLayout(add_buttons_container)
        add_buttons_layout.setContentsMargins(0, 0, 0, 0)
        add_buttons_layout.setSpacing(6)

        self.add_tag_button = QPushButtonWrapper()
        self.add_tag_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_tag_button.setText("Add Tag")

        self.add_field_button = QPushButtonWrapper()
        self.add_field_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_field_button.setText("Add Field")

        add_buttons_layout.addWidget(self.add_tag_button)
        add_buttons_layout.addWidget(self.add_field_button)

        preview_layout.addWidget(self.thumb)
        preview_layout.addWidget(self.thumb.media_player)
        info_layout.addWidget(self.file_attrs)
        info_layout.addWidget(self.fields)

        splitter.addWidget(preview_section)
        splitter.addWidget(info_section)
        # splitter.addWidget(self.libs_flow_container)
        splitter.setStretchFactor(1, 2)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(splitter)
        root_layout.addWidget(add_buttons_container)

    def update_widgets(self) -> bool:
        """Render the panel widgets with the newest data from the Library."""
        # No Items Selected
        # items: list[Entry] = [self.driver.frame_content[x] for x in self.driver.selected]
        if len(self.driver.selected) == 0:
            # TODO: Clear everything to default
            # self.file_attrs.update_blank()
            self.file_attrs.update_stats()
            self.file_attrs.update_date_label()

        # One Item Selected
        elif len(self.driver.selected) == 1:
            entry: Entry = self.lib.get_entry_full(self.driver.selected[0])
            filepath: Path = self.lib.library_dir / entry.path
            ext: str = filepath.suffix.lower()

            stats: dict = self.thumb.update_preview(filepath, ext)
            try:
                self.file_attrs.update_stats(filepath, ext, stats)
                self.file_attrs.update_date_label(filepath)
                self.fields.update_from_entry(entry)
                self.update_add_tag_button(entry)
                self.update_add_field_button(entry)
            except Exception as e:
                logger.error("[Preview Panel] Error updating selection", error=e)
                traceback.print_exc()

        # Multiple Selected Items
        elif len(self.driver.selected) > 1:
            # Render mixed selection
            self.file_attrs.update_multi_selection(len(self.driver.selected))
            self.file_attrs.update_date_label()
            # self.fields.update_from_entries(items)
            # self.file_attrs.update_selection_count()

        # self.thumb.update_widgets()
        # # self.file_attrs.update_widgets()
        # self.fields.update_widgets()

        return True

    def update_add_field_button(self, entry: Entry):
        with catch_warnings(record=True):
            self.add_field_modal.done.disconnect()
            self.add_field_button.clicked.disconnect()
            # TODO: Remove all "is_connected" instances across the codebase
            self.add_field_modal.is_connected = False
            self.add_field_button.is_connected = False

        self.add_field_modal.done.connect(
            lambda f: (
                self.fields.add_field_to_selected(f),
                self.fields.update_from_entry(entry),
            )
        )
        self.add_field_modal.is_connected = True
        self.add_field_button.clicked.connect(self.add_field_modal.show)

    def update_add_tag_button(self, entry: Entry):
        with catch_warnings(record=True):
            self.add_tag_modal.widget.tag_chosen.disconnect()
            self.add_tag_button.clicked.disconnect()

        self.add_tag_modal.widget.tag_chosen.connect(
            lambda t: (
                self.fields.add_tags_to_selected(t),
                self.fields.update_from_entry(entry),
            )
        )

        self.add_tag_button.clicked.connect(
            lambda: (
                self.add_tag_modal.widget.update_tags(),
                self.add_tag_modal.show(),
            )
        )
        self.add_tag_button.is_connected = True

        # self.add_field_button.clicked.connect(self.add_tag_modal.show)
