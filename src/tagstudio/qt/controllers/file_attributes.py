# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import html
import typing
from dataclasses import dataclass
from datetime import datetime as dt
from pathlib import Path
from typing import override

import structlog
from humanfriendly import format_size  # pyright: ignore[reportUnknownVariableType]
from PIL import ImageFont
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QGuiApplication, QPalette
from PySide6.QtWidgets import QSizePolicy, QWidget

from tagstudio.core.enums import ShowFilepathOption
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.media_types import MediaTypes
from tagstudio.core.query_lang.file_groups import SEARCH
from tagstudio.core.utils.decompression import get_display_ext, get_inner_ext
from tagstudio.core.utils.normalization import exists, path_on_disk
from tagstudio.core.utils.str_formatting import format_duration
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.size_animation import SizeAnimation
from tagstudio.qt.utils.file_opener import FileOpenerHelper, open_file
from tagstudio.qt.views.file_attributes_view import FileAttributesView

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)

_NOT_AVAILABLE = "<i>N/A</i>"
_LOADING = "—"


@dataclass
class FileAttributeData:
    width: int | None = None
    height: int | None = None
    duration: int | None = None


class FileAttributes(QWidget):
    """The selected file's name, folder path, and properties."""

    def __init__(self, library: Library, driver: QtDriver) -> None:
        super().__init__()
        self._lib = library
        self._driver = driver

        self._filepath: Path | None = None
        self._folders: list[Path] = []
        self._hovered_folder = ""
        self._is_expanded = True

        self.setLayout(FileAttributesView())
        self._details_animation = SizeAnimation(self.layout().details)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._connect_callbacks()
        self._set_expanded(expanded=True)
        self.update_stats()

    @override
    def layout(self) -> FileAttributesView:
        layout = super().layout()
        assert isinstance(layout, FileAttributesView)
        return layout

    @override
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ThemeChange:
            view = self.layout()
            view.set_toggle_icons()
            view.toggle_button.setIcon(
                view.collapse_icon if self._is_expanded else view.expand_icon
            )
            view.folder_label.setText(self._folder_links())
        super().changeEvent(event)

    def _connect_callbacks(self) -> None:
        view = self.layout()
        view.toggle_button.clicked.connect(self._toggle_details)
        view.folder_label.linkActivated.connect(self._open_folder)
        view.folder_label.linkHovered.connect(self._underline_folder)
        view.ignored_label.clicked.connect(self._driver.open_fix_ignored_entries_modal)
        view.unlinked_label.clicked.connect(self._driver.open_fix_unlinked_entries_modal)
        view.open_file_action.triggered.connect(self._open_file)
        view.open_explorer_action.triggered.connect(self._open_explorer)
        view.copy_filename_action.triggered.connect(self._copy_filename)
        view.copy_path_action.triggered.connect(self._copy_path)

    def update_stats(
        self,
        filepath: Path | None = None,
        stats: FileAttributeData | None = None,
        entry: Entry | None = None,
        reserve_stat_space: bool = False,
    ) -> None:
        """Show a file's name, folder path, and properties."""
        if filepath is None:
            self._show_message(f"<i>{Translations['preview.no_selection']}</i>")
            return
        if stats is None:
            stats = FileAttributeData()

        view = self.layout()
        filepath = path_on_disk(filepath)
        self._filepath = filepath

        view.message_label.setHidden(True)
        view.header.setHidden(False)
        view.details.setHidden(not self._is_expanded)

        ext = get_display_ext(filepath)
        is_linked = exists(filepath)
        view.ext_label.setText(ext.upper()[1:] or filepath.stem.upper())
        is_ignored = Ignore.matcher.is_ignored(filepath.relative_to(unwrap(self._lib.library_dir)))
        view.ignored_label.setHidden(not is_ignored)
        view.unlinked_label.setHidden(is_linked)
        view.name_label.set_file_path(filepath)
        name_font = view.name_label.font()
        name_font.setStrikeOut(is_ignored)
        view.name_label.setFont(name_font)
        self._set_folders(filepath)

        file_size = None
        if entry is not None and entry.file_size is not None:
            file_size = format_size(entry.file_size)
        view.set_property(view.size_label, file_size)

        is_loading_stats = reserve_stat_space and is_linked
        dimensions = None
        if stats.width is not None and stats.height is not None:
            dimensions = f"{stats.width} × {stats.height} px"
        elif is_loading_stats and (
            MediaTypes.contains("image.raster", get_inner_ext(filepath) or ext, SEARCH)
            or MediaTypes.contains("video", ext, SEARCH)
        ):
            dimensions = _LOADING
        view.set_property(view.dimensions_label, dimensions)

        duration = None
        if stats.duration is not None:
            duration = format_duration(stats.duration)
        elif is_loading_stats and (
            MediaTypes.contains("video", ext, SEARCH)
            or MediaTypes.contains("audio", ext, SEARCH)
            or ext in {".apng", ".gif"}  # Usually animated, unlike PNG, WebP, or JPEG XL
        ):
            duration = _LOADING
        view.set_property(view.duration_label, duration)

        font_family, font_style = None, None
        if is_linked and MediaTypes.contains("font", ext, SEARCH):
            try:
                font_family, font_style = ImageFont.truetype(filepath).getname()
            except (FileNotFoundError, OSError) as e:
                logger.error(
                    "[FileAttributes] Could not process file stats", filepath=filepath, error=e
                )
        view.set_property(view.font_family_label, font_family)
        view.set_property(view.font_style_label, font_style)

    def update_dates(self, entry: Entry | None = None) -> None:
        """Show the entry's and its file's dates."""
        view = self.layout()
        if entry is None:
            for label in (view.date_added_label, view.date_created_label, view.date_modified_label):
                view.set_property(label, None)
            return

        added = _NOT_AVAILABLE
        if entry.date_added is not None:
            added = self._driver.settings.format_datetime(entry.date_added)
        view.set_property(view.date_added_label, added)
        view.set_property(view.date_created_label, self._format_timestamp(entry.date_created))
        view.set_property(view.date_modified_label, self._format_timestamp(entry.date_modified))

    def update_multi_selection(self, count: int) -> None:
        """Show how many items are selected."""
        self._show_message(Translations.format("preview.multiple_selection", count=count))

    def _show_message(self, text: str) -> None:
        view = self.layout()
        self._filepath = None
        view.message_label.setText(text)
        view.message_label.setHidden(False)
        view.header.setHidden(True)
        view.details.setHidden(True)

    def _toggle_details(self) -> None:
        self._set_expanded(not self._is_expanded)

    def _set_expanded(self, expanded: bool) -> None:
        view = self.layout()
        self._is_expanded = expanded
        view.toggle_button.setIcon(view.collapse_icon if expanded else view.expand_icon)
        if self._filepath is not None:
            self._details_animation.set_shown(expanded)

    def _set_folders(self, filepath: Path) -> None:
        """List the file's folders."""
        library_dir = unwrap(self._lib.library_dir)
        if self._driver.settings.show_filepath == ShowFilepathOption.SHOW_FULL_PATHS:
            self._folders = [p for p in reversed(filepath.parents) if p.name or p.drive]
        else:
            relative_parents = filepath.relative_to(library_dir).parents
            self._folders = [library_dir / p for p in reversed(relative_parents)]
        self._hovered_folder = ""
        self.layout().folder_label.setText(self._folder_links())

    def _underline_folder(self, index: str) -> None:
        """Underline a folder link."""
        label = self.layout().folder_label
        if index != self._hovered_folder:
            self._hovered_folder = index
            label.setText(self._folder_links())
        # NOTE: Replacing the text resets the hand cursor Qt shows over links
        if index:
            label.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            label.unsetCursor()

    def _folder_links(self) -> str:
        text_color = QGuiApplication.palette().color(QPalette.ColorRole.WindowText).name()
        # Zero width spaces let long folder names wrap anywhere
        links = [
            f"<a href='{i}' style='color: {text_color}; "
            f"text-decoration: {'underline' if str(i) == self._hovered_folder else 'none'}'>"
            f"{html.escape('\u200b'.join(folder.name or folder.drive))}</a>"
            for i, folder in enumerate(self._folders)
        ]
        return " <span style='color: #777777'>›</span> ".join(links)

    def _format_timestamp(self, timestamp: float | None) -> str:
        if timestamp is None:
            return _NOT_AVAILABLE
        return self._driver.settings.format_datetime(dt.fromtimestamp(timestamp))

    def _open_folder(self, index: str) -> None:
        open_file(self._folders[int(index)])

    def _open_file(self) -> None:
        if self._filepath is not None:
            FileOpenerHelper(self._filepath).open_file()

    def _open_explorer(self) -> None:
        if self._filepath is not None:
            FileOpenerHelper(self._filepath).open_explorer()

    def _copy_filename(self) -> None:
        if self._filepath is not None:
            QGuiApplication.clipboard().setText(self._filepath.name)

    def _copy_path(self) -> None:
        if self._filepath is not None:
            QGuiApplication.clipboard().setText(str(self._filepath))
