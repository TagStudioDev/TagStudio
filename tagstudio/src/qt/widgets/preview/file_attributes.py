# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import os
import platform
import typing
from datetime import datetime as dt
from pathlib import Path

import cv2
import structlog
from humanfriendly import format_size
from PIL import Image, ImageFont, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import Qt, Signal
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

    tags_updated = Signal()

    label_bg_color = (
        Theme.COLOR_BG_DARK.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else Theme.COLOR_DARK_LABEL.value
    )

    # panel_bg_color = (
    #     Theme.COLOR_BG_DARK.value
    #     if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
    #     else Theme.COLOR_BG_LIGHT.value
    # )

    file_label_style = "font-size: 12px"
    properties_style = (
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
    date_style = "font-size:12px;"

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()
        # self.is_connected = False
        # self.lib = library
        # self.driver: QtDriver = driver
        # self.initialized = False
        # self.is_open: bool = False

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(6)

        self.file_label = FileOpenerLabel()
        self.file_label.setObjectName("filenameLabel")
        self.file_label.setTextFormat(Qt.TextFormat.RichText)
        self.file_label.setWordWrap(True)
        self.file_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.file_label.setStyleSheet(FileAttributes.file_label_style)

        self.date_created_label = QLabel()
        self.date_created_label.setObjectName("dateCreatedLabel")
        self.date_created_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.date_created_label.setTextFormat(Qt.TextFormat.RichText)
        self.date_created_label.setStyleSheet(FileAttributes.date_style)

        self.date_modified_label = QLabel()
        self.date_modified_label.setObjectName("dateModifiedLabel")
        self.date_modified_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.date_modified_label.setTextFormat(Qt.TextFormat.RichText)
        self.date_modified_label.setStyleSheet(FileAttributes.date_style)

        self.dimensions_label = QLabel()
        self.dimensions_label.setObjectName("dimensionsLabel")
        self.dimensions_label.setWordWrap(True)
        self.dimensions_label.setStyleSheet(FileAttributes.properties_style)

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
        logger.info(filepath)
        if filepath and filepath.is_file():
            created: dt = None
            if platform.system() == "Windows" or platform.system() == "Darwin":
                created = dt.fromtimestamp(filepath.stat().st_birthtime)  # type: ignore[attr-defined, unused-ignore]
            else:
                created = dt.fromtimestamp(filepath.stat().st_ctime)
            modified: dt = dt.fromtimestamp(filepath.stat().st_mtime)
            self.date_created_label.setText(
                f"<b>Date Created:</b> {dt.strftime(created, "%a, %x, %X")}"
            )
            self.date_modified_label.setText(
                f"<b>Date Modified:</b> {dt.strftime(modified, "%a, %x, %X")}"
            )
            self.date_created_label.setHidden(False)
            self.date_modified_label.setHidden(False)
        elif filepath:
            self.date_created_label.setText("<b>Date Created:</b> <i>N/A</i>")
            self.date_modified_label.setText("<b>Date Modified:</b> <i>N/A</i>")
            self.date_created_label.setHidden(False)
            self.date_modified_label.setHidden(False)
        else:
            self.date_created_label.setHidden(True)
            self.date_modified_label.setHidden(True)

    def update_stats(self, filepath: Path | None = None):
        """Render the panel widgets with the newest data from the Library."""
        logger.info("update_stats", selected=filepath)

        if not filepath:
            self.file_label.setText("<i>No Items Selected</i>")
            self.file_label.set_file_path("")
            self.file_label.setCursor(Qt.CursorShape.ArrowCursor)
            self.dimensions_label.setText("")
        else:
            self.file_label.set_file_path(filepath)

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
            # self.open_file_action.triggered.connect(self.opener.open_file)
            # self.open_explorer_action.triggered.connect(self.opener.open_explorer)

            # TODO: Do this all somewhere else, this is just here temporarily.
            ext: str = filepath.suffix.lower()
            try:
                image: Image.Image = Image.open(filepath)
                # Stats for specific file types are displayed here.
                if image and (
                    MediaCategories.is_ext_in_category(
                        ext, MediaCategories.IMAGE_RASTER_TYPES, mime_fallback=True
                    )
                    or MediaCategories.is_ext_in_category(
                        ext, MediaCategories.VIDEO_TYPES, mime_fallback=True
                    )
                    or MediaCategories.is_ext_in_category(
                        ext, MediaCategories.IMAGE_RAW_TYPES, mime_fallback=True
                    )
                ):
                    self.dimensions_label.setText(
                        f"{ext.upper()[1:]}  •  {format_size(filepath.stat().st_size)}\n"
                        f"{image.width} x {image.height} px"
                    )
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.FONT_TYPES, mime_fallback=True
                ):
                    try:
                        font = ImageFont.truetype(filepath)
                        self.dimensions_label.setText(
                            f"{ext.upper()[1:]} •  {format_size(filepath.stat().st_size)}\n"
                            f"{font.getname()[0]} ({font.getname()[1]}) "
                        )
                    except OSError:
                        self.dimensions_label.setText(
                            f"{ext.upper()[1:]}  •  {format_size(filepath.stat().st_size)}"
                        )
                        logger.info(f"[PreviewPanel][ERROR] Couldn't read font file: {filepath}")
                else:
                    self.dimensions_label.setText(f"{ext.upper()[1:]}")
                    self.dimensions_label.setText(
                        f"{ext.upper()[1:]}  •  {format_size(filepath.stat().st_size)}"
                    )
                self.update_date_label(filepath)

                if not filepath.is_file():
                    raise FileNotFoundError

            except (FileNotFoundError, cv2.error) as e:
                self.dimensions_label.setText(f"{ext.upper()[1:]}")
                logger.error("Couldn't render thumbnail", filepath=filepath, error=e)
                self.update_date_label()
            except (
                UnidentifiedImageError,
                DecompressionBombError,  # noqa: F821
            ) as e:
                self.dimensions_label.setText(
                    f"{ext.upper()[1:]}  •  {format_size(filepath.stat().st_size)}"
                )
                logger.error("Couldn't render thumbnail", filepath=filepath, error=e)
                self.update_date_label(filepath)

    def update_multi_selection(self, count: int):
        # Multiple Selected Items
        self.file_label.setText(f"<b>{count}</b> Items Selected")
        self.file_label.setCursor(Qt.CursorShape.ArrowCursor)
        self.file_label.set_file_path("")
        self.dimensions_label.setText("")
