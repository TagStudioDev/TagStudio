# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import traceback
import typing
from pathlib import Path

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QWidget
from src.core.library.alchemy.library import Library
from src.core.library.alchemy.models import Entry
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
        self.is_connected = False
        self.lib = library
        self.driver: QtDriver = driver
        self.initialized = False
        self.is_open: bool = False
        # self.selected: list[int] = []  # New way of tracking items

        self.thumb = PreviewThumb(library, driver)
        self.file_attrs = FileAttributes(library, driver)
        self.fields = FieldContainers(library, driver)

        # info_section = QWidget()
        # info_layout = QVBoxLayout(info_section)
        # info_layout.setContentsMargins(0, 0, 0, 0)
        # info_layout.setSpacing(6)

        # info_layout.addWidget(self.file_attrs)
        # info_layout.addWidget(self.fields.scroll_area)

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

        # splitter.addWidget(self.thumb.image_container)
        # splitter.addWidget(self.thumb.media_player)
        splitter.addWidget(self.thumb)
        splitter.addWidget(self.thumb.media_player)
        splitter.addWidget(self.file_attrs)
        splitter.addWidget(self.fields)
        # splitter.addWidget(self.libs_flow_container)
        splitter.setStretchFactor(3, 2)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(splitter)

    def update_selected_entry(self, driver: "QtDriver"):
        for grid_idx in driver.selected:
            entry = driver.frame_content[grid_idx]
            result = self.lib.get_entry_full(entry.id)
            logger.info(
                "found item",
                grid_idx=grid_idx,
                lookup_id=entry.id,
            )
            self.driver.frame_content[grid_idx] = result

    def update_widgets(self) -> bool:
        """Render the panel widgets with the newest data from the Library."""
        # No Items Selected
        items: list[Entry] = [self.driver.frame_content[x] for x in self.driver.selected]
        if len(self.driver.selected) == 0:
            # TODO: Clear everything to default
            # self.file_attrs.update_blank()
            self.file_attrs.update_stats()
            self.file_attrs.update_date_label()

        # One Item Selected
        elif len(self.driver.selected) == 1:
            entry: Entry = items[0]
            filepath: Path = self.lib.library_dir / entry.path
            ext: str = filepath.suffix.lower()

            stats: dict = self.thumb.update_preview(filepath, ext)
            logger.info("stats", stats=stats, ext=ext)
            try:
                self.file_attrs.update_stats(filepath, ext, stats)
                self.file_attrs.update_date_label(filepath)
                self.fields.update_from_entry(entry)
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
