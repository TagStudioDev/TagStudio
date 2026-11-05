# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

import typing
from datetime import datetime as dt
from enum import IntEnum
from functools import partial
from pathlib import Path
from typing import cast, override
from warnings import catch_warnings

import structlog
from PySide6 import QtCore
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QResizeEvent, QShortcut
from PySide6.QtWidgets import QSplitter, QWidget

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
from tagstudio.i18n.translations import Translations, field_type_name
from tagstudio.qt.controllers.edit_text import EditText
from tagstudio.qt.controllers.file_attributes import FileAttributeData
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.size_animation import SizeAnimation
from tagstudio.qt.controllers.tiles.tile_list import TileList
from tagstudio.qt.mixed.datetime_picker import DatetimePicker
from tagstudio.qt.views.inspector_view import InspectorView
from tagstudio.qt.views.styles.tagstudio_style import set_at_limit

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)

_STARTING_WIDTH = 276


class _ItemMode(IntEnum):
    TAG = 1
    FIELD = 2


class Inspector(QWidget):
    can_add_tags_changed = Signal(bool)

    def __init__(self, driver: QtDriver) -> None:
        super().__init__()
        self._driver = driver
        self._lib = self._driver.lib
        self._settings = self._driver.settings
        self._are_tags_fields_shown = True

        self._current_stats: FileAttributeData | None = None
        self._preview_height_limit: int | None = None  # Max dragged preview area height
        self._preview_outdated = False  # Preview can become outdated if the Inspector is collapsed

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

        self.setLayout(InspectorView(driver=driver, pixel_ratio=self.devicePixelRatio()))
        self._preview_animation = SizeAnimation(self.layout().preview_section)
        self._file_info_animation = SizeAnimation(self.layout().file_attrs)
        self._tags_fields_animation = SizeAnimation(self.layout().containers)
        self._add_buttons_animation = SizeAnimation(self.layout().add_buttons_container)
        self.setStyleSheet("QScrollArea { background: transparent; }")
        self._set_item_mode(None)
        self._connect_callbacks()

    def _connect_callbacks(self) -> None:
        # Tag Search
        self.layout().add_tag_button.clicked.connect(lambda: self._set_item_mode(_ItemMode.TAG))
        self._open_tag_search_action.activated.connect(self._open_tag_search_callback)
        self.layout().tag_search_box.done.connect(partial(self._tag_added_callback))

        # Field Search
        self.layout().add_field_button.clicked.connect(lambda: self._set_item_mode(_ItemMode.FIELD))
        self._open_field_search_action.activated.connect(self._open_field_search_callback)
        self.layout().field_search_box.done.connect(partial(self._field_added_callback))

        # Previews
        self.layout().preview_thumb.stats_updated.connect(self._thumb_stats_updated_callback)
        self.layout().preview_thumb.check_ffmpeg.connect(self._toggle_ffmpeg_warning)
        self.layout().preview_thumb.aspect_ratio_changed.connect(self._fit_preview_height)
        self.layout().preview_splitter.splitterMoved.connect(self._on_preview_splitter_moved)

        self._driver.entry_state.entry_tags_changed.connect(self._on_tags_changed)
        self._driver.entry_state.tags_edited.connect(self._on_tags_edited)
        self._driver.selection.changed.connect(self.update_from_selection)

    def _on_tags_changed(self, entry_ids: set[int]) -> None:
        selected = self._driver.selection.selected
        if len(selected) == 1 and selected[0] in entry_ids:
            self.layout().containers.update_from_entry(selected[0])
            self.layout().tag_search_box.added = self.layout().containers.tags

    def _on_tags_edited(self, tag_ids: set[int]) -> None:  # pyright: ignore[reportUnusedParameter]
        self._on_tags_changed(set(self._driver.selection.selected))

    def _set_item_mode(self, mode: _ItemMode | None):
        def hide_and_disable_buttons():
            self.layout().add_tag_button.setHidden(True)
            self.layout().add_tag_button.setEnabled(False)
            self.layout().add_field_button.setHidden(True)
            self.layout().add_field_button.setEnabled(False)

        def restore_buttons():
            has_selection = bool(self._driver.selection.selected)
            self.layout().add_tag_button.setHidden(False)
            self.layout().add_tag_button.setEnabled(has_selection)
            self.layout().add_field_button.setHidden(False)
            self.layout().add_field_button.setEnabled(has_selection)

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

    def _tag_added_callback(self, query: str):
        if not query or not self._settings.keep_suggest_boxes_open:
            self._set_item_mode(None)
            self.layout().add_tag_button.setFocus()
        else:
            self.layout().tag_search_box.layout().search_field.setFocus()

    def _field_added_callback(self, query: str):
        if not query or not self._settings.keep_suggest_boxes_open:
            self._set_item_mode(None)
            self.layout().add_field_button.setFocus()
        else:
            self.layout().field_search_box.layout().search_field.setFocus()

    def _thumb_stats_updated_callback(self, filepath: Path, stats: FileAttributeData) -> None:
        selected = self._driver.selection.selected
        if len(selected) != 1:
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

        entry = unwrap(self._lib.get_entry(selected[0]))
        self.layout().file_attrs.update_stats(filepath, self._current_stats, entry)
        self._lay_out_info_now()

    def _set_selection_callback(self) -> None:
        with catch_warnings(record=True):
            self.layout().field_search_box.item_chosen.disconnect()
            self.layout().tag_search_box.item_chosen.disconnect()

        self.layout().field_search_box.item_chosen.connect(self._add_field_to_selected)
        self.layout().tag_search_box.item_chosen.connect(self._add_tag_to_selected)

    def _add_field_to_selected(self, template: BaseFieldTemplate) -> None:
        self.layout().containers.add_field_to_selected(template)
        # TODO: Allow editing of fields across multiple entries at once.
        selected = self._driver.selection.selected
        if len(selected) == 1:
            if self._driver.settings.edit_field_on_add:
                entry = unwrap(self._lib.get_entry_full(selected[0]))
                entry_field = None
                if isinstance(template, TextFieldTemplate):
                    entry_field = entry.text_fields[-1]
                elif isinstance(template, DatetimeFieldTemplate):
                    entry_field = entry.datetime_fields[-1]
                if entry_field is not None:
                    self._edit_field(entry.id, entry_field)

            self.layout().containers.update_from_entry(selected[0])

    def _edit_field(self, entry_id: int, field: BaseField) -> None:
        # TODO: A lot of this code is similar to or straight up shared with TileList.
        # It's possible to reuse it later, after a TileList refactor.
        field_type = field_type_name(field.class_name)

        if type(field) is TextField:
            edit_modal = Modal(
                EditText(field.name, field.value, field.is_multiline),
                window_title=f"{Translations['field.edit']} ({field_type})",
                is_savable=True,
                inline_title=False,
            )
            edit_modal.saved_data.connect(
                partial(self.layout().containers.update_text_field_callback, field, entry_id)
            )
            edit_modal.show()
        elif type(field) is DatetimeField:
            edit_modal = Modal(
                DatetimePicker(self._driver, field.name, field.value or dt.now()),
                window_title=f"{Translations['field.edit']} ({field_type})",
                is_savable=True,
                inline_title=False,
            )
            edit_modal.saved_data.connect(
                partial(self.layout().containers.update_datetime_field_callback, field, entry_id)
            )
            edit_modal.show()

    def _add_tag_to_selected(self, tag_id: int) -> None:
        self.layout().containers.add_tags_to_selected(tag_id)

    def _toggle_ffmpeg_warning(self, enable_warning: bool = True) -> None:
        if enable_warning and (not FfmpegStatus.which() or not FfprobeStatus.which()):
            self.layout().warning_banner.show()
            return

        self.layout().warning_banner.hide()

    def update_from_selection(self, update_preview: bool = True) -> None:
        """Update the panel widgets with the selected entries' newest data from the Library.

        Args:
            update_preview (bool): Should the file preview be updated?
            (Only works with one or more items selected)
        """
        selected = self._driver.selection.selected
        self._set_item_mode(None)
        try:
            # No Items Selected
            if len(selected) == 0:
                self.layout().preview_thumb.hide_preview()
                self._current_stats = None
                self.layout().file_attrs.update_stats()
                self.layout().file_attrs.update_dates()
                self.layout().containers.hide_containers()

            # One Item Selected
            elif len(selected) == 1:
                entry_id = selected[0]
                entry: Entry = unwrap(self._lib.get_entry(entry_id))

                filepath: Path = unwrap(self._lib.library_dir) / entry.path
                if filepath != self.layout().preview_thumb.current_file:
                    self._current_stats = None

                if update_preview and self.width() == 0:
                    self.layout().preview_thumb.hide_preview()
                    self._preview_outdated = True
                elif update_preview:
                    self.layout().preview_thumb.display_file(filepath, entry.date_modified)
                    if self._current_stats is None:
                        self._current_stats = FileAttributeData()
                    self.layout().file_attrs.update_stats(
                        filepath, self._current_stats, entry, reserve_stat_space=True
                    )
                self.layout().file_attrs.update_dates(entry)
                self.layout().containers.update_from_entry(entry_id)
                self._set_selection_callback()

            # Multiple Selected Items
            elif len(selected) > 1:
                # items: list[Entry] = [self.lib.get_entry_full(x) for x in self.driver.selected]
                self.layout().preview_thumb.hide_preview()  # TODO: Render mixed selection
                self._current_stats = None
                self.layout().file_attrs.update_multi_selection(len(selected))
                self.layout().file_attrs.update_dates()
                self.layout().containers.hide_containers()  # TODO: Allow for mixed editing
                self._set_selection_callback()

        except Exception as e:
            logger.error("[Inspector] Error updating selection", error=e)
        self._lay_out_info_now()
        self._fit_preview_height()
        self._emit_can_add_tags()

    def _emit_can_add_tags(self) -> None:
        self.can_add_tags_changed.emit(
            self._are_tags_fields_shown and bool(self._driver.selection.selected)
        )

    def _lay_out_info_now(self) -> None:
        """Lay out the file's details now."""
        file_attrs = self.layout().file_attrs
        # Lay out children first so no frame paints between their queued layout passes
        for widget in [*reversed(file_attrs.findChildren(QWidget)), file_attrs]:
            if (layout := QWidget.layout(widget)) is not None:
                layout.activate()
        unwrap(QWidget.layout(unwrap(file_attrs.parentWidget()))).activate()

    def stop_media_playback(self) -> None:
        """Stop any media playback in the inspector."""
        self.layout().preview_thumb.media_player.stop()

    @property
    def containers(self) -> TileList:
        return self.layout().containers

    def _content_height(self) -> int | None:
        """How tall the current preview is when it fills the preview area's width."""
        thumb = self.layout().preview_thumb
        width = self.layout().preview_splitter.width()
        if thumb.current_file is None or width == 0:
            return None
        return round(width / thumb.aspect_ratio)

    def _fit_preview_height(self) -> None:
        """Resize the preview area to its content, up to the dragged height or else a square."""
        if self.width() == 0 or self.layout().preview_section.isHidden():
            return
        splitter = self.layout().preview_splitter
        preview_height, info_height = splitter.sizes()
        height = self._preview_height()
        content_height = self._content_height()
        if height != preview_height:
            splitter.setSizes([height, preview_height + info_height - height])

        lowest, highest = cast(tuple[int, int], splitter.getRange(1))
        position = splitter.handle(1).y()
        is_at_content_height = content_height is not None and height >= content_height
        set_at_limit(splitter, position <= lowest or position >= highest or is_at_content_height)

    def _preview_height(self) -> int:
        """The preview area's height for its content."""
        height = self._preview_height_limit
        if height is None:
            height = self.layout().preview_splitter.width()
        if (content_height := self._content_height()) is not None:
            height = min(height, content_height)
        return height

    def _on_preview_splitter_moved(self) -> None:
        preview_height = self.layout().preview_splitter.sizes()[0]
        content_height = self._content_height()
        if content_height is None or preview_height < content_height:
            self._preview_height_limit = preview_height
        else:
            self._preview_height_limit = max(self._preview_height_limit or 0, content_height)
        self._fit_preview_height()

    def set_preview_shown(self, shown: bool) -> None:
        self._preview_animation.set_shown(shown, self._preview_height())

    def set_file_info_shown(self, shown: bool) -> None:
        self._file_info_animation.set_shown(shown)

    def set_tags_fields_shown(self, shown: bool) -> None:
        self._are_tags_fields_shown = shown
        if not shown:
            self._set_item_mode(None)
        self._tags_fields_animation.set_shown(shown)
        self._add_buttons_animation.set_shown(shown)
        self._open_tag_search_action.setEnabled(shown)
        self._open_field_search_action.setEnabled(shown)
        self._emit_can_add_tags()

    @property
    def is_preview_showing(self) -> bool:
        """Whether the Inspector is showing a file preview."""
        return self.layout().preview_thumb.current_file is not None

    @property
    def preview_section(self) -> QWidget:
        return self.layout().preview_section

    @property
    def preview_widget(self) -> QWidget | None:
        return self.layout().preview_thumb.preview_widget

    @property
    def preview_splitter(self) -> QSplitter:
        return self.layout().preview_splitter

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._fit_preview_height()
        if self._preview_outdated and self.width() > 0:
            self._preview_outdated = False
            self.update_from_selection()

    @override
    def layout(self) -> InspectorView:
        layout = super().layout()
        assert isinstance(layout, InspectorView)
        return layout

    @override
    def sizeHint(self) -> QSize:
        return QSize(_STARTING_WIDTH, super().sizeHint().height())
