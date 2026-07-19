# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from pathlib import Path
from warnings import catch_warnings

import structlog
from PySide6 import QtCore
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy.fields import BaseFieldTemplate
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.ffmpeg_status import FfmpegStatus, FfprobeStatus
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.field_containers import FieldContainers
from tagstudio.qt.mixed.file_attributes import FileAttributeData
from tagstudio.qt.views.preview_panel_view import PreviewPanelView

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class PreviewPanel(QWidget):
    def __init__(self, driver: "QtDriver") -> None:
        super().__init__()
        self._layout = PreviewPanelView(driver=driver, pixel_ratio=self.devicePixelRatio())
        self._driver = driver
        self._lib = self._driver.lib
        self._selected: list[int]
        self._current_stats: FileAttributeData | None = None

        key = QtCore.QKeyCombination(
            QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
            QtCore.Qt.Key.Key_T,
        )
        self._add_tag_action = QShortcut(key, self)

        self.setLayout(self._layout)
        self._connect_callbacks()

    def _connect_callbacks(self) -> None:
        self._layout.add_field_button.clicked.connect(self._add_field_button_callback)
        self._layout.add_tag_button.clicked.connect(self._add_tag_button_callback)
        self._layout.preview_thumb.stats_updated.connect(self._thumb_stats_updated_callback)
        self._add_tag_action.activated.connect(self._layout.add_tag_button.setFocus)
        self._add_tag_action.activated.connect(self._layout.add_tag_button.click)
        self._layout.tag_search_box.done.connect(self.tag_added_callback)
        self._layout.tag_search_box.tags_updated.connect(self._update_added_callback)
        self._layout.preview_thumb.check_ffmpeg.connect(self._toggle_ffmpeg_warning)

    def _add_field_button_callback(self) -> None:
        # self.__add_field_modal.show()
        pass

    def _add_tag_button_callback(self) -> None:
        self._layout.tag_search_box.added = self._layout.containers.tags
        self._layout.tag_search_box.layout().search_field.setDisabled(False)
        self._layout.tag_search_box.setHidden(False)
        self._layout.add_tag_button.setHidden(True)
        self._layout.add_field_button.setHidden(True)

    def tag_added_callback(self):
        self._layout.tag_search_box.setHidden(True)
        self._layout.add_tag_button.setHidden(False)
        self._layout.add_field_button.setHidden(False)

        self._layout.add_tag_button.setFocus()

    def _update_added_callback(self):
        self._layout.tag_search_box.added = self._layout.containers.tags

    def _thumb_stats_updated_callback(self, filepath: Path, stats: FileAttributeData) -> None:
        if len(self._selected) != 1:
            return

        if filepath != self._layout.preview_thumb.current_file:
            return

        if self._current_stats is None:
            self._current_stats = FileAttributeData()

        if stats.width is not None:
            self._current_stats.width = stats.width
        if stats.height is not None:
            self._current_stats.height = stats.height
        if stats.duration is not None:
            self._current_stats.duration = stats.duration

        self._layout.file_attrs.update_stats(filepath, self._current_stats)

    def _set_selection_callback(self) -> None:
        with catch_warnings(record=True):
            self._layout.field_search_box.field_template_chosen.disconnect()
            self._layout.tag_search_box.item_chosen.disconnect()

        self._layout.field_search_box.field_template_chosen.connect(self._add_field_to_selected)
        self._layout.tag_search_box.item_chosen.connect(self._add_tag_to_selected)

    def _add_field_to_selected(self, template: BaseFieldTemplate) -> None:
        self._layout.containers.add_field_to_selected(template)
        if len(self._selected) == 1:
            self._layout.containers.update_from_entry(self._selected[0])

    def _add_tag_to_selected(self, tag_id: int) -> None:
        self._layout.containers.add_tags_to_selected(tag_id)
        if len(self._selected) == 1:
            self._layout.containers.update_from_entry(self._selected[0])

    def _toggle_ffmpeg_warning(self, enable_warning: bool = True) -> None:
        if enable_warning and (not FfmpegStatus.which() or not FfprobeStatus.which()):
            self._layout.warning_banner.show()
            return

        self._layout.warning_banner.hide()

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
                self._layout.preview_thumb.hide_preview()
                self._current_stats = None
                self._layout.file_attrs.update_stats()
                self._layout.file_attrs.update_date_label()
                self._layout.containers.hide_containers()

                self._layout.add_tag_button.setEnabled(False)
                self._layout.add_field_button.setEnabled(False)
                self._layout.add_tag_button.setHidden(False)
                self._layout.add_field_button.setHidden(False)
                self._layout.tag_search_box.hide_and_reset()

            # One Item Selected
            elif len(selected) == 1:
                entry_id = selected[0]
                entry: Entry = unwrap(self._lib.get_entry(entry_id))

                filepath: Path = unwrap(self._lib.library_dir) / entry.path
                if filepath != self._layout.preview_thumb.current_file:
                    self._current_stats = None

                if update_preview:
                    stats: FileAttributeData = self._layout.preview_thumb.display_file(filepath)
                    self._current_stats = stats
                    self._layout.file_attrs.update_stats(filepath, stats)
                self._layout.file_attrs.update_date_label(filepath)
                self._layout.containers.update_from_entry(entry_id)

                self._set_selection_callback()

                self._layout.add_tag_button.setEnabled(True)
                self._layout.add_field_button.setEnabled(True)
                self._layout.add_tag_button.setHidden(False)
                self._layout.add_field_button.setHidden(False)
                self._layout.tag_search_box.hide_and_reset()

            # Multiple Selected Items
            elif len(selected) > 1:
                # items: list[Entry] = [self.lib.get_entry_full(x) for x in self.driver.selected]
                self._layout.preview_thumb.hide_preview()  # TODO: Render mixed selection
                self._current_stats = None
                self._layout.file_attrs.update_multi_selection(len(selected))
                self._layout.file_attrs.update_date_label()
                self._layout.containers.hide_containers()  # TODO: Allow for mixed editing

                self._set_selection_callback()

                self._layout.add_tag_button.setEnabled(True)
                self._layout.add_field_button.setEnabled(True)
                self._layout.add_tag_button.setHidden(False)
                self._layout.add_field_button.setHidden(False)
                self._layout.tag_search_box.hide_and_reset()

        except Exception as e:
            logger.error("[Preview Panel] Error updating selection", error=e)

    def stop_media_playback(self) -> None:
        """Stop any media playback in the preview panel."""
        self._layout.preview_thumb.media_player.stop()

    @property
    def containers(self) -> FieldContainers:
        return self._layout.containers
