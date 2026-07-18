# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
import traceback
import typing
from pathlib import Path

import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSplitter, QVBoxLayout, QWidget

from tagstudio.core.constants import FFMPEG_HELP_URL
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.field_template_search_panel_controller import FieldTemplateSearchPanel
from tagstudio.qt.controllers.preview_thumb_controller import PreviewThumb
from tagstudio.qt.controllers.return_button import ReturnButton
from tagstudio.qt.controllers.tag_suggest_box import TagSuggestBox
from tagstudio.qt.mixed.field_containers import FieldContainers
from tagstudio.qt.mixed.file_attributes import FileAttributeData, FileAttributes
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.field_template_search_panel_view import FieldTemplateSearchPanelView
from tagstudio.qt.views.stylesheets.stylesheets import button_style, preview_warning_style
from tagstudio.qt.views.suggest_box_view import SuggestBoxView

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class PreviewPanelView(QWidget):
    _selected: list[int]

    def __init__(self, driver: "QtDriver") -> None:
        super().__init__()
        self._lib = driver.lib
        rm = ResourceManager()

        self.field_search_box: FieldTemplateSearchPanel = FieldTemplateSearchPanel(
            self._lib,
            is_field_template_chooser=True,
            view=FieldTemplateSearchPanelView(is_field_template_chooser=True),
        )

        tag_placeholder = " ".join(
            [Translations["home.search_or_create_tags"], Translations["home.search.how_to_exit"]]
        )
        self.tag_search_box = TagSuggestBox(
            driver, view=SuggestBoxView(placeholder_text=tag_placeholder)
        )
        self.tag_search_box.hide()

        self._thumb = PreviewThumb(self._lib, driver)
        self._file_attrs = FileAttributes(self._lib, driver)
        self._containers = FieldContainers(
            self._lib, driver
        )  # TODO: this should be name mangled, but is still needed on the controller side atm

        # Visual Preview
        preview_section = QWidget()
        preview_layout = QVBoxLayout(preview_section)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(6)

        # Warning Banner (Missing FFmpeg, etc.)
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

        # File Information
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

        self._add_tag_button = ReturnButton(Translations["tag.add"])
        self._add_tag_button.setEnabled(False)
        self._add_tag_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_tag_button.setMinimumHeight(30)
        self._add_tag_button.setStyleSheet(button_style())

        self._add_field_button = ReturnButton(Translations["field.add"])
        self._add_field_button.setEnabled(False)
        self._add_field_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_field_button.setMinimumHeight(30)
        self._add_field_button.setStyleSheet(button_style())

        add_buttons_layout.addWidget(self._add_tag_button)
        add_buttons_layout.addWidget(self._add_field_button)
        add_buttons_layout.addWidget(self.tag_search_box)
        # add_buttons_layout.addWidget(self.field_search)

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
                self._file_attrs.update_stats()
                self._file_attrs.update_date_label()
                self._containers.hide_containers()

                self._add_tag_button.setEnabled(False)
                self._add_field_button.setEnabled(False)
                self._add_tag_button.setHidden(False)
                self._add_field_button.setHidden(False)
                self.tag_search_box.hide_and_reset()

            # One Item Selected
            elif len(selected) == 1:
                entry_id = selected[0]
                entry: Entry = unwrap(self._lib.get_entry(entry_id))

                filepath: Path = unwrap(self._lib.library_dir) / entry.path
                if filepath != self._thumb.current_file:
                    self.__current_stats = None

                if update_preview:
                    stats: FileAttributeData = self._thumb.display_file(filepath)
                    self.__current_stats = stats
                    self._file_attrs.update_stats(filepath, stats)
                self._file_attrs.update_date_label(filepath)
                self._containers.update_from_entry(entry_id)

                self._set_selection_callback()

                self._add_tag_button.setEnabled(True)
                self._add_field_button.setEnabled(True)
                self._add_tag_button.setHidden(False)
                self._add_field_button.setHidden(False)
                self.tag_search_box.hide_and_reset()

            # Multiple Selected Items
            elif len(selected) > 1:
                # items: list[Entry] = [self.lib.get_entry_full(x) for x in self.driver.selected]
                self._thumb.hide_preview()  # TODO: Render mixed selection
                self.__current_stats = None
                self._file_attrs.update_multi_selection(len(selected))
                self._file_attrs.update_date_label()
                self._containers.hide_containers()  # TODO: Allow for mixed editing

                self._set_selection_callback()

                self._add_tag_button.setEnabled(True)
                self._add_field_button.setEnabled(True)
                self._add_tag_button.setHidden(False)
                self._add_field_button.setHidden(False)
                self.tag_search_box.hide_and_reset()

        except Exception as e:
            logger.error("[Preview Panel] Error updating selection", error=e)
            traceback.print_exc()

    @property
    def add_buttons_enabled(self) -> bool:  # needed for the tests
        field = self._add_field_button.isEnabled()
        tag = self._add_tag_button.isEnabled()
        assert field == tag
        return field

    @add_buttons_enabled.setter
    def add_buttons_enabled(self, enabled: bool) -> None:
        self._add_field_button.setEnabled(enabled)
        self._add_tag_button.setEnabled(enabled)

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
