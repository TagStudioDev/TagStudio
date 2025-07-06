# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import traceback
import typing
from pathlib import Path

import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qt.controller.widgets.preview.preview_thumb_controller import PreviewThumb

from tagstudio.core.enums import Theme
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.preview.field_containers import FieldContainers
from tagstudio.qt.widgets.preview.file_attributes import FileAttributes

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)

BUTTON_STYLE = f"""
    QPushButton{{
        background-color: {Theme.COLOR_BG.value};
        border-radius: 6px;
        font-weight: 500;
        text-align: center;
    }}
    QPushButton::hover{{
        background-color: {Theme.COLOR_HOVER.value};
        border-color: {get_ui_color(ColorType.BORDER, UiColor.THEME_DARK)};
        border-style: solid;
        border-width: 2px;
    }}
    QPushButton::pressed{{
        background-color: {Theme.COLOR_PRESSED.value};
        border-color: {get_ui_color(ColorType.LIGHT_ACCENT, UiColor.THEME_DARK)};
        border-style: solid;
        border-width: 2px;
    }}
    QPushButton::disabled{{
        background-color: {Theme.COLOR_DISABLED_BG.value};
    }}
"""


class PreviewPanelView(QWidget):
    lib: Library

    _selected: list[int]

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()
        self.lib = library

        self.__thumb = PreviewThumb(self.lib, driver)
        self.__file_attrs = FileAttributes(self.lib, driver)
        self._fields = FieldContainers(
            self.lib, driver
        )  # TODO: this should be name mangled, but is still needed on the controller side atm

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

        self.__add_tag_button = QPushButton(Translations["tag.add"])
        self.__add_tag_button.setEnabled(False)
        self.__add_tag_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.__add_tag_button.setMinimumHeight(28)
        self.__add_tag_button.setStyleSheet(BUTTON_STYLE)

        self.__add_field_button = QPushButton(Translations["library.field.add"])
        self.__add_field_button.setEnabled(False)
        self.__add_field_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.__add_field_button.setMinimumHeight(28)
        self.__add_field_button.setStyleSheet(BUTTON_STYLE)

        add_buttons_layout.addWidget(self.__add_tag_button)
        add_buttons_layout.addWidget(self.__add_field_button)

        preview_layout.addWidget(self.__thumb)
        info_layout.addWidget(self.__file_attrs)
        info_layout.addWidget(self._fields)

        splitter.addWidget(preview_section)
        splitter.addWidget(info_section)
        splitter.setStretchFactor(1, 2)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(splitter)
        root_layout.addWidget(add_buttons_container)

        self.__connect_callbacks()

    def __connect_callbacks(self):
        self.__add_field_button.clicked.connect(self._add_field_button_callback)
        self.__add_tag_button.clicked.connect(self._add_tag_button_callback)

    def _add_field_button_callback(self):
        raise NotImplementedError()

    def _add_tag_button_callback(self):
        raise NotImplementedError()

    def _set_selection_callback(self):
        raise NotImplementedError()

    def set_selection(self, selected: list[int], update_preview: bool = True):
        """Render the panel widgets with the newest data from the Library.

        Args:
            selected  (list[int]): List of the IDs of the selected entries.
            update_preview (bool): Should the file preview be updated?
            (Only works with one or more items selected)
        """
        self._selected = selected
        try:
            # No Items Selected
            if len(selected) == 0:
                self.__thumb.hide_preview()
                self.__file_attrs.update_stats()
                self.__file_attrs.update_date_label()
                self._fields.hide_containers()

                self.add_buttons_enabled = False

            # One Item Selected
            elif len(selected) == 1:
                entry_id = selected[0]
                entry: Entry | None = self.lib.get_entry(entry_id)
                assert entry is not None

                assert self.lib.library_dir is not None
                filepath: Path = self.lib.library_dir / entry.path

                if update_preview:
                    stats: dict = self.__thumb.display_file(filepath)
                    self.__file_attrs.update_stats(filepath, stats)
                self.__file_attrs.update_date_label(filepath)
                self._fields.update_from_entry(entry_id)

                self._set_selection_callback()

                self.add_buttons_enabled = True

            # Multiple Selected Items
            elif len(selected) > 1:
                # items: list[Entry] = [self.lib.get_entry_full(x) for x in self.driver.selected]
                self.__thumb.hide_preview()  # TODO: Render mixed selection
                self.__file_attrs.update_multi_selection(len(selected))
                self.__file_attrs.update_date_label()
                self._fields.hide_containers()  # TODO: Allow for mixed editing

                self._set_selection_callback()

                self.add_buttons_enabled = True

        except Exception as e:
            logger.error("[Preview Panel] Error updating selection", error=e)
            traceback.print_exc()

    @property
    def add_buttons_enabled(self) -> bool:  # needed for the tests
        field = self.__add_field_button.isEnabled()
        tag = self.__add_tag_button.isEnabled()
        assert field == tag
        return field

    @add_buttons_enabled.setter
    def add_buttons_enabled(self, enabled: bool):
        self.__add_field_button.setEnabled(enabled)
        self.__add_tag_button.setEnabled(enabled)

    @property
    def _file_attributes_widget(self) -> FileAttributes:  # needed for the tests
        """Getter for the file attributes widget."""
        return self.__file_attrs

    @property
    def field_containers_widget(self) -> FieldContainers:  # needed for the tests
        """Getter for the field containers widget."""
        return self._fields

    @property
    def preview_thumb(self) -> PreviewThumb:
        return self.__thumb
