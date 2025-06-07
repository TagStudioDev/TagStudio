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
from tagstudio.qt.widgets.preview.field_containers import FieldContainers
from tagstudio.qt.widgets.preview.file_attributes import FileAttributes
from tagstudio.qt.widgets.preview.preview_thumb import PreviewThumb

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)

BUTTON_STYLE = (
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


class PreviewPanelView(QWidget):
    lib: Library

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()
        self.lib = library

        self.__thumb = PreviewThumb(self.lib, driver)
        self.__file_attrs = FileAttributes(self.lib, driver)
        self.__fields = FieldContainers(self.lib, driver)

        self._tag_search_panel = TagSearchPanel(self.lib, is_tag_chooser=True)

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
        info_layout.addWidget(self.__fields)

        splitter.addWidget(preview_section)
        splitter.addWidget(info_section)
        splitter.setStretchFactor(1, 2)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(splitter)
        root_layout.addWidget(add_buttons_container)

        self.__connect_callbacks()

    def __connect_callbacks(self):
        self.__add_tag_button.clicked.connect(self._add_tag_button_callback)

    def add_tag_button_enabled(self) -> bool:  # needed for the tests
        """Returns whether the 'Add Tag' Button is enabled."""
        return self.__add_tag_button.isEnabled()

    def add_field_button_enabled(self) -> bool:  # needed for the tests
        """Returns whether the 'Add Field' Button is enabled."""
        return self.__add_field_button.isEnabled()

    @property
    def _file_attributes_widget(self) -> FileAttributes:  # needed for the tests
        """Getter for the file attributes widget."""
        return self.__file_attrs

    @property
    def _field_containers_widget(self) -> FieldContainers:  # needed for the tests
        """Getter for the field containers widget."""
        return self.__fields  # TODO: try to remove non-test uses of this

    def thumb_media_player_stop(self):
        self.__thumb.media_player.stop()

    def _add_tag_button_callback(self):
        raise NotImplementedError()

    def update_view(self, selected: list[int], update_preview: bool = True):
        """Render the panel widgets with the newest data from the Library.

        Args:
            selected  (list[int]): List of the IDs of the selected entries.
            update_preview (bool): Should the file preview be updated?
            (Only works with one or more items selected)
        """
        # No Items Selected
        try:
            if len(selected) == 0:
                self.__thumb.hide_preview()
                self.__file_attrs.update_stats()
                self.__file_attrs.update_date_label()
                self.__fields.hide_containers()

                self.__add_tag_button.setEnabled(False)
                self.__add_field_button.setEnabled(False)

            # One Item Selected
            elif len(selected) == 1:
                entry_id = selected[0]
                entry: Entry | None = self.lib.get_entry(entry_id)
                assert entry is not None

                assert self.lib.library_dir is not None
                filepath: Path = self.lib.library_dir / entry.path

                if update_preview:
                    stats: dict = self.__thumb.update_preview(filepath)
                    self.__file_attrs.update_stats(filepath, stats)
                self.__file_attrs.update_date_label(filepath)
                self.__fields.update_from_entry(entry_id)
                self.__update_add_tag_button(entry_id)
                self.__update_add_field_button(entry_id)

                self.__add_tag_button.setEnabled(True)
                self.__add_field_button.setEnabled(True)

            # Multiple Selected Items
            elif len(selected) > 1:
                # items: list[Entry] = [self.lib.get_entry_full(x) for x in self.driver.selected]
                self.__thumb.hide_preview()  # TODO: Render mixed selection
                self.__file_attrs.update_multi_selection(len(selected))
                self.__file_attrs.update_date_label()
                self.__fields.hide_containers()  # TODO: Allow for mixed editing
                self.__update_add_tag_button()
                self.__update_add_field_button()

                self.__add_tag_button.setEnabled(True)
                self.__add_field_button.setEnabled(True)

        except Exception as e:
            logger.error("[Preview Panel] Error updating selection", error=e)
            traceback.print_exc()

    def __update_add_field_button(self, entry_id: int | None = None):
        with catch_warnings(record=True):
            self.add_field_modal.done.disconnect()
            self.__add_field_button.clicked.disconnect()

        self.add_field_modal.done.connect(
            lambda f: (
                self.__fields.add_field_to_selected(f),
                (self.__fields.update_from_entry(entry_id) if entry_id else ()),
            )
        )
        self.__add_field_button.clicked.connect(self.add_field_modal.show)

    def __update_add_tag_button(self, entry_id: int | None = None):
        with catch_warnings(record=True):
            self._tag_search_panel.tag_chosen.disconnect()
            self.__add_tag_button.clicked.disconnect()

        self._tag_search_panel.tag_chosen.connect(
            lambda t: (
                self.__fields.add_tags_to_selected(t),
                (self.__fields.update_from_entry(entry_id) if entry_id else ()),
            )
        )
