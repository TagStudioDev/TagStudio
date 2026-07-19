# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from datetime import datetime as dt
from enum import IntEnum
from functools import partial
from pathlib import Path
from typing import override
from warnings import catch_warnings

import structlog
from PySide6 import QtCore
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy.fields import (
    BaseField,
    BaseFieldTemplate,
    DatetimeField,
    DatetimeFieldTemplate,
    TextField,
    TextFieldTemplate,
)
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.ffmpeg_status import FfmpegStatus, FfprobeStatus
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.edit_text_controller import EditText
from tagstudio.qt.mixed.datetime_picker import DatetimePicker
from tagstudio.qt.mixed.field_containers import FieldContainers
from tagstudio.qt.mixed.file_attributes import FileAttributeData
from tagstudio.qt.translations import FIELD_TYPE_KEYS, Translations
from tagstudio.qt.views.panel_modal import PanelModal
from tagstudio.qt.views.preview_panel_view import PreviewPanelView

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class _ItemMode(IntEnum):
    TAG = 1
    FIELD = 2


class PreviewPanel(QWidget):
    def __init__(self, driver: "QtDriver") -> None:
        super().__init__()
        self._driver = driver
        self._lib = self._driver.lib
        self._selected: list[int]
        self._current_stats: FileAttributeData | None = None

        self._open_tag_search_action = QShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_T,
            ),
            self,
        )
        self._open_field_search_action = QShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_L,
            ),
            self,
        )

        self.setLayout(PreviewPanelView(driver=driver, pixel_ratio=self.devicePixelRatio()))
        self._set_item_mode(None)
        self._connect_callbacks()

    def _connect_callbacks(self) -> None:
        # Tag Search
        self.layout().add_tag_button.clicked.connect(lambda: self._set_item_mode(_ItemMode.TAG))
        self._open_tag_search_action.activated.connect(self._open_tag_search_callback)
        self.layout().tag_search_box.done.connect(self._tag_added_callback)
        self.layout().containers.on_tags_update.connect(self._update_added_callback)

        # Field Search
        self.layout().add_field_button.clicked.connect(lambda: self._set_item_mode(_ItemMode.FIELD))
        self._open_field_search_action.activated.connect(self._open_field_search_callback)
        self.layout().field_search_box.done.connect(self._field_added_callback)

        # Previews
        self.layout().preview_thumb.stats_updated.connect(self._thumb_stats_updated_callback)
        self.layout().preview_thumb.check_ffmpeg.connect(self._toggle_ffmpeg_warning)

    def _set_item_mode(self, mode: _ItemMode | None):
        def hide_and_disable_buttons():
            self.layout().add_tag_button.setHidden(True)
            self.layout().add_tag_button.setEnabled(False)
            self.layout().add_field_button.setHidden(True)
            self.layout().add_field_button.setEnabled(False)

        def restore_buttons():
            self.layout().add_tag_button.setHidden(False)
            self.layout().add_tag_button.setEnabled(True)
            self.layout().add_field_button.setHidden(False)
            self.layout().add_field_button.setEnabled(True)

        if mode == _ItemMode.TAG:
            self.layout().tag_search_box.added = self.layout().containers.tags
            self.layout().field_search_box.hide_and_reset()
            self.layout().tag_search_box.setHidden(False)
            hide_and_disable_buttons()
        elif mode == _ItemMode.FIELD:
            self.layout().tag_search_box.hide_and_reset()
            self.layout().field_search_box.setHidden(False)
            hide_and_disable_buttons()
        else:
            self.layout().tag_search_box.hide_and_reset()
            self.layout().field_search_box.hide_and_reset()
            restore_buttons()

    def _open_tag_search_callback(self) -> None:
        self.layout().add_tag_button.setFocus()
        self.layout().add_tag_button.click()

    def _open_field_search_callback(self) -> None:
        self.layout().add_field_button.setFocus()
        self.layout().add_field_button.click()

    def _tag_added_callback(self):
        self._set_item_mode(None)
        self.layout().add_tag_button.setFocus()

    def _field_added_callback(self):
        self._set_item_mode(None)
        self.layout().add_field_button.setFocus()

    def _update_added_callback(self):
        self.layout().tag_search_box.added = self.layout().containers.tags

    def _thumb_stats_updated_callback(self, filepath: Path, stats: FileAttributeData) -> None:
        if len(self._selected) != 1:
            return

        if filepath != self.layout().preview_thumb.current_file:
            return

        if self._current_stats is None:
            self._current_stats = FileAttributeData()

        if stats.width is not None:
            self._current_stats.width = stats.width
        if stats.height is not None:
            self._current_stats.height = stats.height
        if stats.duration is not None:
            self._current_stats.duration = stats.duration

        self.layout().file_attrs.update_stats(filepath, self._current_stats)

    def _set_selection_callback(self) -> None:
        with catch_warnings(record=True):
            self.layout().field_search_box.item_chosen.disconnect()
            self.layout().tag_search_box.item_chosen.disconnect()

        self.layout().field_search_box.item_chosen.connect(self._add_field_to_selected)
        self.layout().tag_search_box.item_chosen.connect(self._add_tag_to_selected)

    def _add_field_to_selected(self, template: BaseFieldTemplate) -> None:
        self.layout().containers.add_field_to_selected(template)
        # TODO: Allow editing of fields across multiple entries at once.
        if len(self._selected) == 1:
            if self._driver.settings.edit_field_on_add:
                entry = unwrap(self._lib.get_entry_full(self._selected[0]))
                entry_field = None
                if isinstance(template, TextFieldTemplate):
                    entry_field = entry.text_fields[-1]
                elif isinstance(template, DatetimeFieldTemplate):
                    entry_field = entry.datetime_fields[-1]
                if entry_field is not None:
                    self._edit_field(entry.id, entry_field)

            self.layout().containers.update_from_entry(self._selected[0])

    def _edit_field(self, entry_id: int, field: BaseField) -> None:
        # TODO: A lot of this code is similar to or straight up shared with FieldContainers.
        # It's possible to reuse it later, after a FieldContainers refactor.
        field_name_key: str = FIELD_TYPE_KEYS.get(field.class_name, "field_type.unknown")

        if type(field) is TextField:
            edit_modal = PanelModal(
                EditText(field.name, field.value, field.is_multiline),
                window_title=f"{Translations['field.edit']} ({Translations[field_name_key]})",
                is_savable=True,
                inline_title=False,
            )
            edit_modal.saved_data.connect(
                partial(self.layout().containers.update_text_field_callback, field, entry_id)
            )
            edit_modal.show()
        elif type(field) is DatetimeField:
            edit_modal = PanelModal(
                DatetimePicker(self._driver, field.name, field.value or dt.now()),
                window_title=f"{Translations['field.edit']} ({Translations[field_name_key]})",
                is_savable=True,
                inline_title=False,
            )
            edit_modal.saved_data.connect(
                partial(self.layout().containers.update_datetime_field_callback, field, entry_id)
            )
            edit_modal.show()

    def _add_tag_to_selected(self, tag_id: int) -> None:
        self.layout().containers.add_tags_to_selected(tag_id)
        if len(self._selected) == 1:
            self.layout().containers.update_from_entry(self._selected[0])

    def _toggle_ffmpeg_warning(self, enable_warning: bool = True) -> None:
        if enable_warning and (not FfmpegStatus.which() or not FfprobeStatus.which()):
            self.layout().warning_banner.show()
            return

        self.layout().warning_banner.hide()

    def set_selection(self, selected: list[int], update_preview: bool = True) -> None:
        """Render the panel widgets with the newest data from the Library.

        Args:
            selected  (list[int]): List of the IDs of the selected entries.
            update_preview (bool): Should the file preview be updated?
            (Only works with one or more items selected)
        """
        self._selected = selected
        self._set_item_mode(None)
        try:
            # No Items Selected
            if len(selected) == 0:
                self.layout().preview_thumb.hide_preview()
                self._current_stats = None
                self.layout().file_attrs.update_stats()
                self.layout().file_attrs.update_date_label()
                self.layout().containers.hide_containers()
                self.layout().add_tag_button.setEnabled(False)
                self.layout().add_field_button.setEnabled(False)

            # One Item Selected
            elif len(selected) == 1:
                entry_id = selected[0]
                entry: Entry = unwrap(self._lib.get_entry(entry_id))

                filepath: Path = unwrap(self._lib.library_dir) / entry.path
                if filepath != self.layout().preview_thumb.current_file:
                    self._current_stats = None

                if update_preview:
                    stats: FileAttributeData = self.layout().preview_thumb.display_file(filepath)
                    self._current_stats = stats
                    self.layout().file_attrs.update_stats(filepath, stats)
                self.layout().file_attrs.update_date_label(filepath)
                self.layout().containers.update_from_entry(entry_id)
                self._set_selection_callback()

            # Multiple Selected Items
            elif len(selected) > 1:
                # items: list[Entry] = [self.lib.get_entry_full(x) for x in self.driver.selected]
                self.layout().preview_thumb.hide_preview()  # TODO: Render mixed selection
                self._current_stats = None
                self.layout().file_attrs.update_multi_selection(len(selected))
                self.layout().file_attrs.update_date_label()
                self.layout().containers.hide_containers()  # TODO: Allow for mixed editing
                self._set_selection_callback()

        except Exception as e:
            logger.error("[Preview Panel] Error updating selection", error=e)

    def stop_media_playback(self) -> None:
        """Stop any media playback in the preview panel."""
        self.layout().preview_thumb.media_player.stop()

    @property
    def containers(self) -> FieldContainers:
        return self.layout().containers

    @override
    def layout(self) -> PreviewPanelView:
        """Return the typed layout for this widget."""
        return super().layout()  # pyright: ignore[reportReturnType]
