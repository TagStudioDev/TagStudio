# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from pathlib import Path
from typing import override
from warnings import catch_warnings

import structlog
from PySide6 import QtCore
from PySide6.QtGui import QShortcut

from tagstudio.core.library.alchemy.fields import BaseFieldTemplate
from tagstudio.core.utils.ffmpeg_status import FfmpegStatus, FfprobeStatus
from tagstudio.qt.mixed.file_attributes import FileAttributeData
from tagstudio.qt.views.preview_panel_view import PreviewPanelView

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class PreviewPanel(PreviewPanelView):
    def __init__(self, driver: "QtDriver") -> None:
        super().__init__(driver)

        self.__current_stats: FileAttributeData | None = None
        self._thumb.check_ffmpeg.connect(self._toggle_ffmpeg_warning)

        key = QtCore.QKeyCombination(
            QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
            QtCore.Qt.Key.Key_T,
        )
        self.add_tag_action = QShortcut(key, self)

        self.__connect_callbacks()

    def __connect_callbacks(self) -> None:
        self._add_field_button.clicked.connect(self._add_field_button_callback)
        self._add_tag_button.clicked.connect(self._add_tag_button_callback)
        self._thumb.stats_updated.connect(self.__thumb_stats_updated_callback)
        self.add_tag_action.activated.connect(self._add_tag_button.setFocus)
        self.add_tag_action.activated.connect(self._add_tag_button.click)

        self.tag_search_box.done.connect(self.tag_added_callback)
        self.tag_search_box.tags_updated.connect(self.update_added_callback)

    def _add_field_button_callback(self) -> None:
        # self.__add_field_modal.show()
        pass

    def _add_tag_button_callback(self) -> None:
        self.tag_search_box.added = self._containers.tags
        self.tag_search_box.layout().search_field.setDisabled(False)
        self.tag_search_box.setHidden(False)
        self._add_tag_button.setHidden(True)
        self._add_field_button.setHidden(True)

    def tag_added_callback(self):
        self.tag_search_box.setHidden(True)
        self._add_tag_button.setHidden(False)
        self._add_field_button.setHidden(False)

        self._add_tag_button.setFocus()

    def update_added_callback(self):
        self.tag_search_box.added = self._containers.tags

    def __thumb_stats_updated_callback(self, filepath: Path, stats: FileAttributeData) -> None:
        if len(self._selected) != 1:
            return

        if filepath != self._thumb.current_file:
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

    @override
    def _set_selection_callback(self) -> None:
        with catch_warnings(record=True):
            self.field_search_box.field_template_chosen.disconnect()
            self.tag_search_box.item_chosen.disconnect()

        self.field_search_box.field_template_chosen.connect(self._add_field_to_selected)
        self.tag_search_box.item_chosen.connect(self._add_tag_to_selected)

    def _add_field_to_selected(self, template: BaseFieldTemplate) -> None:
        self._containers.add_field_to_selected(template)
        if len(self._selected) == 1:
            self._containers.update_from_entry(self._selected[0])

    def _add_tag_to_selected(self, tag_id: int) -> None:
        self._containers.add_tags_to_selected(tag_id)
        if len(self._selected) == 1:
            self._containers.update_from_entry(self._selected[0])

    def _toggle_ffmpeg_warning(self, enable_warning: bool = True) -> None:
        if enable_warning and (not FfmpegStatus.which() or not FfprobeStatus.which()):
            self._ffmpeg_warning_widget.show()
            return

        self._ffmpeg_warning_widget.hide()
