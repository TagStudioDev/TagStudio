# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
import traceback
import typing
from pathlib import Path

import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.constants import FFMPEG_HELP_URL
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.preview_thumb_controller import PreviewThumb
from tagstudio.qt.mixed.field_containers import FieldContainers
from tagstudio.qt.mixed.file_attributes import FileAttributeData, FileAttributes
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.stylesheets.stylesheets import button_style, preview_warning_style

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class PreviewPanelView(QWidget):
    lib: Library

    _selected: list[int]

    def __init__(self, library: Library, driver: "QtDriver") -> None:
        super().__init__()
        self.lib = library
        rm = ResourceManager()

        self._thumb = PreviewThumb(self.lib, driver)
        self._file_attrs = FileAttributes(self.lib, driver)
        self._containers = FieldContainers(
            self.lib, driver
        )  # TODO: this should be name mangled, but is still needed on the controller side atm
        self.__current_stats: FileAttributeData | None = None
        self.__current_stats_filepath: Path | None = None

        preview_section = QWidget()
        preview_layout = QVBoxLayout(preview_section)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(6)

        self._ffmpeg_warning_widget = QWidget()
        self._ffmpeg_warning_widget.setObjectName("ffmpeg_widget")
        ffmpeg_warning_layout = QHBoxLayout(self._ffmpeg_warning_widget)
        ffmpeg_warning_layout.setContentsMargins(3, 3, 3, 3)
        self._ffmpeg_warning_widget.setStyleSheet(preview_warning_style())
        ffmpeg_warning_label = QLabel(
            Translations.format(
                "preview.missing_module.multimedia",
                module=f'<a href="{FFMPEG_HELP_URL}">FFmpeg</a>',
            )
        )
        ffmpeg_warning_label.setWordWrap(True)
        ffmpeg_warning_label.linkActivated.connect(
            lambda x: QDesktopServices.openUrl(FFMPEG_HELP_URL)
        )
        warning_icon = QLabel()
        warning_icon_pixmap = rm.alert.scaled(
            math.floor(20 * self.devicePixelRatio()), math.floor(20 * self.devicePixelRatio())
        )
        warning_icon_pixmap.setDevicePixelRatio(self.devicePixelRatio())
        warning_icon.setPixmap(warning_icon_pixmap)
        ffmpeg_warning_layout.addWidget(warning_icon)
        ffmpeg_warning_layout.addWidget(ffmpeg_warning_label)
        ffmpeg_warning_layout.setStretch(1, 1)

        self._ffmpeg_warning_widget.hide()

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
        self.__add_tag_button.setStyleSheet(button_style())

        self.__add_field_button = QPushButton(Translations["field.add"])
        self.__add_field_button.setEnabled(False)
        self.__add_field_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.__add_field_button.setMinimumHeight(28)
        self.__add_field_button.setStyleSheet(button_style())

        add_buttons_layout.addWidget(self.__add_tag_button)
        add_buttons_layout.addWidget(self.__add_field_button)

        preview_layout.addWidget(self._thumb)
        info_layout.addWidget(self._ffmpeg_warning_widget)
        info_layout.addWidget(self._file_attrs)
        info_layout.addWidget(self._containers)

        splitter.addWidget(preview_section)
        splitter.addWidget(info_section)
        splitter.setStretchFactor(1, 2)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(splitter)
        root_layout.addWidget(add_buttons_container)

        self.__connect_callbacks()

    def __connect_callbacks(self) -> None:
        self.__add_field_button.clicked.connect(self._add_field_button_callback)
        self.__add_tag_button.clicked.connect(self._add_tag_button_callback)
        self._thumb.stats_updated.connect(self.__thumb_stats_updated_callback)

    def _add_field_button_callback(self) -> None:
        raise NotImplementedError()

    def _add_tag_button_callback(self) -> None:
        raise NotImplementedError()

    def __thumb_stats_updated_callback(self, filepath: Path, stats: FileAttributeData) -> None:
        if len(self._selected) != 1:
            return

        if filepath != self.__current_stats_filepath:
            return

        if self.__current_stats is None:
            self.__current_stats = FileAttributeData()

        if stats.width is not None:
            self.__current_stats.width = stats.width
        if stats.height is not None:
            self.__current_stats.height = stats.height
        if stats.duration is not None:
            self.__current_stats.duration = stats.duration

        self._file_attrs.update_stats(filepath, self.__current_stats)

    def _set_selection_callback(self) -> None:
        raise NotImplementedError()

    def set_selection(self, selected: list[int], update_preview: bool = True) -> None:
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
                self._thumb.hide_preview()
                self.__current_stats = None
                self.__current_stats_filepath = None
                self._file_attrs.update_stats()
                self._file_attrs.update_date_label()
                self._containers.hide_containers()

                self.add_buttons_enabled = False

            # One Item Selected
            elif len(selected) == 1:
                entry_id = selected[0]
                entry: Entry = unwrap(self.lib.get_entry(entry_id))

                filepath: Path = unwrap(self.lib.library_dir) / entry.path
                if filepath != self.__current_stats_filepath:
                    self.__current_stats = None
                    self.__current_stats_filepath = filepath

                if update_preview:
                    stats: FileAttributeData = self._thumb.display_file(filepath)
                    self.__current_stats = stats
                    self._file_attrs.update_stats(filepath, stats)
                self._file_attrs.update_date_label(filepath)
                self._containers.update_from_entry(entry_id)

                self._set_selection_callback()

                self.add_buttons_enabled = True

            # Multiple Selected Items
            elif len(selected) > 1:
                # items: list[Entry] = [self.lib.get_entry_full(x) for x in self.driver.selected]
                self._thumb.hide_preview()  # TODO: Render mixed selection
                self.__current_stats = None
                self.__current_stats_filepath = None
                self._file_attrs.update_multi_selection(len(selected))
                self._file_attrs.update_date_label()
                self._containers.hide_containers()  # TODO: Allow for mixed editing

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
    def add_buttons_enabled(self, enabled: bool) -> None:
        self.__add_field_button.setEnabled(enabled)
        self.__add_tag_button.setEnabled(enabled)

    @property
    def _file_attributes_widget(self) -> FileAttributes:  # needed for the tests
        """Getter for the file attributes widget."""
        return self._file_attrs

    @property
    def field_containers_widget(self) -> FieldContainers:  # needed for the tests
        """Getter for the field containers widget."""
        return self._containers

    @property
    def preview_thumb(self) -> PreviewThumb:
        return self._thumb
