# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import os
import platform
import typing
from datetime import datetime as dt
from datetime import timedelta
from pathlib import Path

import structlog
from humanfriendly import format_size
from PIL import ImageFont
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from tagstudio.core.enums import ShowFilepathOption, Theme
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaCategories
from tagstudio.qt.helpers.file_opener import FileOpenerHelper, FileOpenerLabel
from tagstudio.qt.translations import Translations

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class FileAttributes(QWidget):
    """The Preview Panel Widget."""

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        label_bg_color = (
            Theme.COLOR_BG_DARK.value
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.COLOR_DARK_LABEL.value
        )

        self.date_style = "font-size:12px;"
        self.file_label_style = "font-size: 12px"
        self.properties_style = (
            f"background-color:{label_bg_color};"
            "color:#FFFFFF;"
            "font-family:Oxanium;"
            "font-weight:bold;"
            "font-size:12px;"
            "border-radius:3px;"
            "padding-top: 4px;"
            "padding-right: 1px;"
            "padding-bottom: 1px;"
            "padding-left: 1px;"
        )

        self.file_label = FileOpenerLabel()
        self.file_label.setObjectName("filenameLabel")
        self.file_label.setTextFormat(Qt.TextFormat.RichText)
        self.file_label.setWordWrap(True)
        self.file_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.file_label.setStyleSheet(self.file_label_style)

        self.date_created_label = QLabel()
        self.date_created_label.setObjectName("dateCreatedLabel")
        self.date_created_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.date_created_label.setTextFormat(Qt.TextFormat.RichText)
        self.date_created_label.setStyleSheet(self.date_style)
        self.date_created_label.setHidden(True)

        self.date_modified_label = QLabel()
        self.date_modified_label.setObjectName("dateModifiedLabel")
        self.date_modified_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.date_modified_label.setTextFormat(Qt.TextFormat.RichText)
        self.date_modified_label.setStyleSheet(self.date_style)
        self.date_modified_label.setHidden(True)

        self.dimensions_label = QLabel()
        self.dimensions_label.setObjectName("dimensionsLabel")
        self.dimensions_label.setWordWrap(True)
        self.dimensions_label.setStyleSheet(self.properties_style)
        self.dimensions_label.setHidden(True)

        self.date_container = QWidget()
        date_layout = QVBoxLayout(self.date_container)
        date_layout.setContentsMargins(0, 2, 0, 0)
        date_layout.setSpacing(0)
        date_layout.addWidget(self.date_created_label)
        date_layout.addWidget(self.date_modified_label)

        root_layout.addWidget(self.file_label)
        root_layout.addWidget(self.date_container)
        root_layout.addWidget(self.dimensions_label)
        self.library = library
        self.driver = driver

    def update_date_label(self, filepath: Path | None = None) -> None:
        """Update the "Date Created" and "Date Modified" file property labels."""
        if filepath and filepath.is_file():
            created: dt
            if platform.system() == "Windows" or platform.system() == "Darwin":
                created = dt.fromtimestamp(filepath.stat().st_birthtime)  # type: ignore[attr-defined, unused-ignore]
            else:
                created = dt.fromtimestamp(filepath.stat().st_ctime)
            modified: dt = dt.fromtimestamp(filepath.stat().st_mtime)
            self.date_created_label.setText(
                f"<b>{Translations['file.date_created']}:</b>"
                + f" {self.driver.settings.format_datetime(created)}"
            )
            self.date_modified_label.setText(
                f"<b>{Translations['file.date_modified']}:</b> "
                f"{self.driver.settings.format_datetime(modified)}"
            )
            self.date_created_label.setHidden(False)
            self.date_modified_label.setHidden(False)
        elif filepath:
            self.date_created_label.setText(
                f"<b>{Translations['file.date_created']}:</b> <i>N/A</i>"
            )
            self.date_modified_label.setText(
                f"<b>{Translations['file.date_modified']}:</b> <i>N/A</i>"
            )
            self.date_created_label.setHidden(False)
            self.date_modified_label.setHidden(False)
        else:
            self.date_created_label.setHidden(True)
            self.date_modified_label.setHidden(True)

    def update_stats(self, filepath: Path | None = None, stats: dict | None = None):
        """Render the panel widgets with the newest data from the Library."""
        if not stats:
            stats = {}

        if not filepath:
            self.layout().setSpacing(0)
            self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_label.setText(f"<i>{Translations['preview.no_selection']}</i>")
            self.file_label.set_file_path("")
            self.file_label.setCursor(Qt.CursorShape.ArrowCursor)
            self.dimensions_label.setText("")
            self.dimensions_label.setHidden(True)
        else:
            ext = filepath.suffix.lower()
            self.library_path = self.library.library_dir
            display_path = filepath
            if self.driver.settings.show_filepath == ShowFilepathOption.SHOW_FULL_PATHS:
                display_path = filepath
            elif self.driver.settings.show_filepath == ShowFilepathOption.SHOW_RELATIVE_PATHS:
                assert self.library_path is not None
                display_path = Path(filepath).relative_to(self.library_path)
            elif self.driver.settings.show_filepath == ShowFilepathOption.SHOW_FILENAMES_ONLY:
                display_path = Path(filepath.name)

            self.layout().setSpacing(6)
            self.file_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.file_label.set_file_path(filepath)
            self.dimensions_label.setHidden(False)

            file_str: str = ""
            separator: str = f"<a style='color: #777777'><b>{os.path.sep}</a>"  # Gray
            for i, part in enumerate(display_path.parts):
                part_ = part.strip(os.path.sep)
                if i != len(display_path.parts) - 1:
                    file_str += f"{'\u200b'.join(part_)}{separator}</b>"
                else:
                    if file_str != "":
                        file_str += "<br>"
                    file_str += f"<b>{'\u200b'.join(part_)}</b>"
            self.file_label.setText(file_str)
            self.file_label.setCursor(Qt.CursorShape.PointingHandCursor)
            self.opener = FileOpenerHelper(filepath)

            # Initialize the possible stat variables
            stats_label_text = ""
            ext_display: str = ""
            file_size: str = ""
            width_px_text: str = ""
            height_px_text: str = ""
            duration_text: str = ""
            font_family: str = ""

            # Attempt to populate the stat variables
            width_px_text = stats.get("width", "")
            height_px_text = stats.get("height", "")
            duration_text = stats.get("duration", "")
            font_family = stats.get("font_family", "")
            ext_display = ext.upper()[1:] or filepath.stem.upper()
            if filepath:
                try:
                    file_size = format_size(filepath.stat().st_size)

                    if MediaCategories.is_ext_in_category(
                        ext, MediaCategories.FONT_TYPES, mime_fallback=True
                    ):
                        font = ImageFont.truetype(filepath)
                        font_family = f"{font.getname()[0]} ({font.getname()[1]}) "
                except (FileNotFoundError, OSError) as e:
                    logger.error(
                        "[FileAttributes] Could not process file stats", filepath=filepath, error=e
                    )

            # Format and display any stat variables
            def add_newline(stats_label_text: str) -> str:
                if stats_label_text and stats_label_text[-2:] != "\n":
                    return stats_label_text + "\n"
                return stats_label_text

            if ext_display:
                stats_label_text += ext_display
                if file_size:
                    stats_label_text += f"  •  {file_size}"
            elif file_size:
                stats_label_text += file_size

            if width_px_text and height_px_text:
                stats_label_text = add_newline(stats_label_text)
                stats_label_text += f"{width_px_text} x {height_px_text} px"

            if duration_text:
                stats_label_text = add_newline(stats_label_text)
                try:
                    dur_str = str(timedelta(seconds=float(duration_text)))[:-7]
                    if dur_str.startswith("0:"):
                        dur_str = dur_str[2:]
                    if dur_str.startswith("0"):
                        dur_str = dur_str[1:]
                except OverflowError:
                    dur_str = "-:--"
                stats_label_text += f"{dur_str}"

            if font_family:
                stats_label_text = add_newline(stats_label_text)
                stats_label_text += f"{font_family}"

            self.dimensions_label.setText(stats_label_text)

    def update_multi_selection(self, count: int):
        """Format attributes for multiple selected items."""
        self.layout().setSpacing(0)
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setText(Translations.format("preview.multiple_selection", count=count))
        self.file_label.setCursor(Qt.CursorShape.ArrowCursor)
        self.file_label.set_file_path("")
        self.dimensions_label.setText("")
        self.dimensions_label.setHidden(True)
