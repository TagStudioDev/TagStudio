# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from shutil import which
from warnings import catch_warnings

from tagstudio.core.library.alchemy.fields import BaseFieldTemplate
from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.controllers.field_template_search_panel_controller import FieldTemplateSearchModal
from tagstudio.qt.controllers.tag_search_panel_controller import TagSearchModal
from tagstudio.qt.previews.vendored.ffmpeg import FFMPEG_CMD, FFPROBE_CMD
from tagstudio.qt.views.preview_panel_view import PreviewPanelView

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class PreviewPanel(PreviewPanelView):
    def __init__(self, library: Library, driver: "QtDriver") -> None:
        super().__init__(library, driver)

        self.__add_field_modal = FieldTemplateSearchModal(self.lib, is_field_template_chooser=True)
        self.__add_tag_modal = TagSearchModal(self.lib, is_tag_chooser=True)
        self._thumb.check_ffmpeg.connect(self._toggle_ffmpeg_warning)

    @typing.override
    def _add_field_button_callback(self) -> None:
        self.__add_field_modal.show()

    @typing.override
    def _add_tag_button_callback(self) -> None:
        self.__add_tag_modal.show()

    @typing.override
    def _set_selection_callback(self) -> None:
        with catch_warnings(record=True):
            self.__add_field_modal.search_panel.field_template_chosen.disconnect()
            self.__add_tag_modal.tsp.item_chosen.disconnect()

        self.__add_field_modal.search_panel.field_template_chosen.connect(
            self._add_field_to_selected
        )
        self.__add_tag_modal.tsp.item_chosen.connect(self._add_tag_to_selected)

    def _add_field_to_selected(self, template: BaseFieldTemplate) -> None:
        self._containers.add_field_to_selected(template)
        if len(self._selected) == 1:
            self._containers.update_from_entry(self._selected[0])

    def _add_tag_to_selected(self, tag_id: int) -> None:
        self._containers.add_tags_to_selected(tag_id)
        if len(self._selected) == 1:
            self._containers.update_from_entry(self._selected[0])

    def _toggle_ffmpeg_warning(self, enable_warning: bool = True) -> None:
        if enable_warning and (not which(FFMPEG_CMD) or not which(FFPROBE_CMD)):
            self._ffmpeg_warning_widget.show()
            return

        self._ffmpeg_warning_widget.hide()
