# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import traceback
import typing
from pathlib import Path
from warnings import catch_warnings

import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSplitter, QVBoxLayout, QWidget

from tagstudio.core.enums import Theme
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.modals.add_field import AddFieldModal
from tagstudio.qt.modals.tag_search import TagSearchPanel
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.panel import PanelModal
from tagstudio.qt.widgets.preview.field_containers import FieldContainers
from tagstudio.qt.widgets.preview.file_attributes import FileAttributes
from tagstudio.qt.widgets.preview.preview_thumb import PreviewThumb

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class PreviewPanel(QWidget):
    """The Preview Panel Widget."""

    # TODO: There should be a global button theme somewhere.
    button_style = (
        f"QPushButton{{"
        f"background-color:{Theme.COLOR_BG.value};"
        "border-radius:6px;"
        "font-weight: 500;"
        "text-align: center;"
        f"}}"
        f"QPushButton::hover{{"
        f"background-color:{Theme.COLOR_HOVER.value};"
        f"border-color:{get_ui_color(ColorType.BORDER, UiColor.THEME_DARK)};"
        f"border-style:solid;"
        f"border-width: 2px;"
        f"}}"
        f"QPushButton::pressed{{"
        f"background-color:{Theme.COLOR_PRESSED.value};"
        f"border-color:{get_ui_color(ColorType.LIGHT_ACCENT, UiColor.THEME_DARK)};"
        f"border-style:solid;"
        f"border-width: 2px;"
        f"}}"
        f"QPushButton::disabled{{"
        f"background-color:{Theme.COLOR_DISABLED_BG.value};"
        f"}}"
    )

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver: QtDriver = driver
        self.initialized = False
        self.is_open: bool = True

        self.thumb = PreviewThumb(library, driver)
        self.file_attrs = FileAttributes(library, driver)
        self.fields = FieldContainers(library, driver)

        self.tag_search_panel = TagSearchPanel(self.driver.lib, is_tag_chooser=True)
        self.add_tag_modal = PanelModal(self.tag_search_panel, Translations["tag.add.plural"])
        self.add_tag_modal.setWindowTitle(Translations["tag.add.plural"])

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

        add_buttons_container = QWidget()
        add_buttons_layout = QHBoxLayout(add_buttons_container)
        add_buttons_layout.setContentsMargins(0, 0, 0, 0)
        add_buttons_layout.setSpacing(6)

        self.add_tag_button = QPushButton(Translations["tag.add"])
        self.add_tag_button.setEnabled(False)
        self.add_tag_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_tag_button.setMinimumHeight(28)
        self.add_tag_button.setStyleSheet(PreviewPanel.button_style)

        self.add_field_button = QPushButton(Translations["library.field.add"])
        self.add_field_button.setEnabled(False)
        self.add_field_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_field_button.setMinimumHeight(28)
        self.add_field_button.setStyleSheet(PreviewPanel.button_style)

        add_buttons_layout.addWidget(self.add_tag_button)
        add_buttons_layout.addWidget(self.add_field_button)

        preview_layout.addWidget(self.thumb)
        info_layout.addWidget(self.file_attrs)
        info_layout.addWidget(self.fields)

        splitter.addWidget(preview_section)
        splitter.addWidget(info_section)
        splitter.setStretchFactor(1, 2)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(splitter)
        root_layout.addWidget(add_buttons_container)

    def update_widgets(self, update_preview: bool = True) -> bool:
        """Render the panel widgets with the newest data from the Library.

        Args:
            update_preview(bool): Should the file preview be updated?
            (Only works with one or more items selected)
        """
        # No Items Selected
        try:
            if len(self.driver.selected) == 0:
                self.thumb.hide_preview()
                self.file_attrs.update_stats()
                self.file_attrs.update_date_label()
                self.fields.hide_containers()

                self.add_tag_button.setEnabled(False)
                self.add_field_button.setEnabled(False)

            # One Item Selected
            elif len(self.driver.selected) == 1:
                entry: Entry = self.lib.get_entry(self.driver.selected[0])
                entry_id = self.driver.selected[0]
                filepath: Path = self.lib.library_dir / entry.path
                ext: str = filepath.suffix.lower()

                if update_preview:
                    stats: dict = self.thumb.update_preview(filepath, ext)
                    self.file_attrs.update_stats(filepath, ext, stats)
                self.file_attrs.update_date_label(filepath)
                self.fields.update_from_entry(entry_id)
                self.update_add_tag_button(entry_id)
                self.update_add_field_button(entry_id)

                self.add_tag_button.setEnabled(True)
                self.add_field_button.setEnabled(True)

            # Multiple Selected Items
            elif len(self.driver.selected) > 1:
                # items: list[Entry] = [self.lib.get_entry_full(x) for x in self.driver.selected]
                self.thumb.hide_preview()  # TODO: Render mixed selection
                self.file_attrs.update_multi_selection(len(self.driver.selected))
                self.file_attrs.update_date_label()
                self.fields.hide_containers()  # TODO: Allow for mixed editing
                self.update_add_tag_button()
                self.update_add_field_button()

                self.add_tag_button.setEnabled(True)
                self.add_field_button.setEnabled(True)

            return True
        except Exception as e:
            logger.error("[Preview Panel] Error updating selection", error=e)
            traceback.print_exc()
            return False

    def update_add_field_button(self, entry_id: int | None = None):
        with catch_warnings(record=True):
            self.add_field_modal.done.disconnect()
            self.add_field_button.clicked.disconnect()

        self.add_field_modal.done.connect(
            lambda f: (
                self.fields.add_field_to_selected(f),
                (self.fields.update_from_entry(entry_id) if entry_id else ()),
            )
        )
        self.add_field_button.clicked.connect(self.add_field_modal.show)

    def update_add_tag_button(self, entry_id: int = None):
        with catch_warnings(record=True):
            self.tag_search_panel.tag_chosen.disconnect()
            self.add_tag_button.clicked.disconnect()

        self.tag_search_panel.tag_chosen.connect(
            lambda t: (
                self.fields.add_tags_to_selected(t),
                (self.fields.update_from_entry(entry_id) if entry_id else ()),
            )
        )

        self.add_tag_button.clicked.connect(self.add_tag_modal.show)
