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
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)
from src.core.enums import Theme
from src.core.library.alchemy.library import Library
from src.core.media_types import MediaCategories
from src.qt.helpers.file_opener import FileOpenerHelper, FileOpenerLabel

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

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

    def update_date_label(self, filepath: Path | None = None) -> None:
        """Update the "Date Created" and "Date Modified" file property labels."""
        if filepath and filepath.is_file():
            created: dt = None
            if platform.system() == "Windows" or platform.system() == "Darwin":
                created = dt.fromtimestamp(filepath.stat().st_birthtime)  # type: ignore[attr-defined, unused-ignore]
            else:
                created = dt.fromtimestamp(filepath.stat().st_ctime)
            modified: dt = dt.fromtimestamp(filepath.stat().st_mtime)
            self.date_created_label.setText(
                f"<b>Date Created:</b> {dt.strftime(created, "%a, %x, %X")}"  # TODO: Translate
            )
            self.date_modified_label.setText(
                f"<b>Date Modified:</b> {dt.strftime(modified, "%a, %x, %X")}"  # TODO: Translate
            )
            self.date_created_label.setHidden(False)
            self.date_modified_label.setHidden(False)
        elif filepath:
            self.date_created_label.setText("<b>Date Created:</b> <i>N/A</i>")  # TODO: Translate
            self.date_modified_label.setText("<b>Date Modified:</b> <i>N/A</i>")  # TODO: Translate
            self.date_created_label.setHidden(False)
            self.date_modified_label.setHidden(False)
        else:
            self.date_created_label.setHidden(True)
            self.date_modified_label.setHidden(True)

    def update_stats(self, filepath: Path | None = None, ext: str = ".", stats: dict = None):
        """Render the panel widgets with the newest data from the Library."""
        if not stats:
            stats = {}

        if not filepath:
            self.layout().setSpacing(0)
            self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_label.setText("<i>No Items Selected</i>")  # TODO: Translate
            self.file_label.set_file_path("")
            self.file_label.setCursor(Qt.CursorShape.ArrowCursor)
            self.dimensions_label.setText("")
            self.dimensions_label.setHidden(True)
        else:
            self.layout().setSpacing(6)
            self.file_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.file_label.set_file_path(filepath)
            self.dimensions_label.setHidden(False)

            file_str: str = ""
            separator: str = f"<a style='color: #777777'><b>{os.path.sep}</a>"  # Gray
            for i, part in enumerate(filepath.parts):
                part_ = part.strip(os.path.sep)
                if i != len(filepath.parts) - 1:
                    file_str += f"{"\u200b".join(part_)}{separator}</b>"
                else:
                    file_str += f"<br><b>{"\u200b".join(part_)}</b>"
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
            if ext:
                ext_display = ext.upper()[1:]
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
                dur_str = str(timedelta(seconds=float(duration_text)))[:-7]
                if dur_str.startswith("0:"):
                    dur_str = dur_str[2:]
                if dur_str.startswith("0"):
                    dur_str = dur_str[1:]
                stats_label_text += f"{dur_str}"

            if font_family:
                stats_label_text = add_newline(stats_label_text)
                stats_label_text += f"{font_family}"

            self.dimensions_label.setText(stats_label_text)

    def update_multi_selection(self, count: int):
        """Format attributes for multiple selected items."""
        self.layout().setSpacing(0)
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setText(f"<b>{count}</b> Items Selected")  # TODO: Translate
        self.file_label.setCursor(Qt.CursorShape.ArrowCursor)
        self.file_label.set_file_path("")
        self.dimensions_label.setText("")
        self.dimensions_label.setHidden(True)
