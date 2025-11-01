# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import os
import platform
import typing
from dataclasses import dataclass
from datetime import datetime as dt
from pathlib import Path

import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from tagstudio.core.enums import ShowFilepathOption, Theme
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.models.preview_panel.attributes.file_attributes_model import FilePropertyType
from tagstudio.qt.translations import Translations
from tagstudio.qt.utils.file_opener import FileOpenerLabel
from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


@dataclass
class FileAttributeData:
    width: int | None = None
    height: int | None = None
    duration: int | None = None


FILE_NAME_LABEL_STYLE = "font-size: 12px;"

DATE_LABEL_STYLE = "font-size: 12px;"


class FileAttributesView(QWidget):
    """A widget displaying a list of a file's attributes."""

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()
        self.library = library
        self.driver = driver

        label_bg_color = (
            Theme.COLOR_BG_DARK.value
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.COLOR_BG_LIGHT.value
        )
        properties_style = f"""
            background-color: {label_bg_color};
            color: #FFFFFF;
            font-family: Oxanium;
            font-weight: bold;
            font-size: 12px;
            border-radius: 3px;
            padding-top: 4px;
            padding-right: 1px;
            padding-bottom: 1px;
            padding-left: 1px;
        """

        self.__root_layout = QVBoxLayout(self)
        self.__root_layout.setContentsMargins(0, 0, 0, 0)
        self.__root_layout.setSpacing(6)

        # File name
        self.file_path_label = FileOpenerLabel()
        self.file_path_label.setObjectName("file_path_label")
        self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.file_path_label.setWordWrap(True)
        self.file_path_label.setTextFormat(Qt.TextFormat.RichText)
        self.file_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.file_path_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.file_path_label.setStyleSheet(FILE_NAME_LABEL_STYLE)

        self.__root_layout.addWidget(self.file_path_label)

        # Date container
        self.date_properties = QWidget()
        self.date_properties.setObjectName("date_properties")

        self.date_properties_layout = QVBoxLayout(self.date_properties)
        self.date_properties_layout.setObjectName("date_properties_layout")
        self.date_properties_layout.setContentsMargins(0, 2, 0, 0)
        self.date_properties_layout.setSpacing(0)

        self.__root_layout.addWidget(self.date_properties)

        # Date created
        self.date_created_label = QLabel()
        self.date_created_label.setObjectName("date_created_label")
        self.date_created_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.date_created_label.setTextFormat(Qt.TextFormat.RichText)
        self.date_created_label.setStyleSheet(DATE_LABEL_STYLE)
        self.date_created_label.setHidden(True)

        self.date_properties_layout.addWidget(self.date_created_label)

        # Date modified
        self.date_modified_label = QLabel()
        self.date_modified_label.setObjectName("date_modified_label")
        self.date_modified_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.date_modified_label.setTextFormat(Qt.TextFormat.RichText)
        self.date_modified_label.setStyleSheet(DATE_LABEL_STYLE)
        self.date_modified_label.setHidden(True)

        self.date_properties_layout.addWidget(self.date_modified_label)

        # File properties
        self.properties = QWidget()
        self.properties.setObjectName("properties")
        self.properties.setStyleSheet(properties_style)

        self.properties_layout = QVBoxLayout(self.properties)
        self.properties_layout.setObjectName("properties_layout")
        self.properties_layout.setContentsMargins(0, 0, 0, 0)
        self.properties_layout.setSpacing(0)

        self.__root_layout.addWidget(self.properties)

        self.__property_widgets: dict[FilePropertyType, FilePropertyWidget] = {}

    def update_file_path(self, file_path: Path) -> None:
        self.file_path_label.set_file_path(file_path)

        # Format the path according to the user's settings
        display_path: Path = file_path
        match self.driver.settings.show_filepath:
            case ShowFilepathOption.SHOW_FULL_PATHS:
                display_path = file_path
            case ShowFilepathOption.SHOW_RELATIVE_PATHS:
                display_path = Path(file_path).relative_to(unwrap(self.library.library_dir))
            case ShowFilepathOption.SHOW_FILENAMES_ONLY:
                display_path = Path(file_path.name)

        # Stringify the path
        path_string: str = ""
        path_separator: str = f"<a style='color: #777777'><b>{os.path.sep}</b></a>"  # Gray
        for i, part in enumerate(display_path.parts):
            directory_name = part.strip(os.path.sep)
            if i < len(display_path.parts) - 1:
                path_string += f"{'\u200b'.join(directory_name)}{path_separator}</b>"
            else:
                if path_string != "":
                    path_string += "<br>"
                path_string += f"<b>{'\u200b'.join(directory_name)}</b>"

        self.file_path_label.setText(path_string)

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

    def update_file_property(self, property_type: FilePropertyType, **kwargs) -> None:
        """Update a property of the file."""
        logger.debug("[FileAttributes] Updating file property", type=property_type, **kwargs)

        if property_type not in self.__property_widgets:
            property_widget: FilePropertyWidget = property_type.widget_class()
            self.__property_widgets[property_type] = property_widget
            self.properties_layout.addWidget(property_widget)

        self.__property_widgets[property_type].set_value(**kwargs)

    # def update_stats(self, filepath: Path | None = None, stats: FileAttributeData | None = None):
    #     """Render the panel widgets with the newest data from the Library."""
    #     if not stats:
    #         stats = FileAttributeData()
    #
    #     else:
    #         ext = filepath.suffix.lower()
    #
    #         # Attempt to populate the stat variables
    #         ext_display = ext.upper()[1:] or filepath.stem.upper()
    #         if filepath and filepath.is_file():
    #             try:
    #                 file_size = format_size(filepath.stat().st_size)
    #
    #                 if MediaCategories.is_ext_in_category(
    #                     ext, MediaCategories.FONT_TYPES, mime_fallback=True
    #                 ):
    #                     font = ImageFont.truetype(filepath)
    #                     font_family = f"{font.getname()[0]} ({font.getname()[1]}) "
    #             except (FileNotFoundError, OSError) as e:
    #                 logger.error(
    #                     "[FileAttributes] Could not process file stats", filepath=filepath, error=e
    #                 )
    #
    #         # Format and display any stat variables
    #         def add_newline(stats_label_text: str) -> str:
    #             if stats_label_text and stats_label_text[-4:] != "<br>":
    #                 return stats_label_text + "<br>"
    #             return stats_label_text
    #
    #         if ext_display:
    #             stats_label_text += ext_display
    #             red = get_ui_color(ColorType.PRIMARY, UiColor.RED)
    #             orange = get_ui_color(ColorType.PRIMARY, UiColor.ORANGE)
    #
    #             if Ignore.compiled_patterns and Ignore.compiled_patterns.match(
    #                 filepath.relative_to(unwrap(self.library.library_dir))
    #             ):
    #                 stats_label_text = (
    #                     f"{stats_label_text}"
    #                     f"  •  <span style='color:{orange}'>"
    #                     f"{Translations['preview.ignored'].upper()}</span>"
    #                 )
    #             if not filepath.exists():
    #                 stats_label_text = (
    #                     f"{stats_label_text}"
    #                     f"  •  <span style='color:{red}'>"
    #                     f"{Translations['preview.unlinked'].upper()}</span>"
    #                 )
    #             if file_size:
    #                 stats_label_text += f"  •  {file_size}"
    #         elif file_size:
    #             stats_label_text += file_size
    #
    #         if font_family:
    #             stats_label_text = add_newline(stats_label_text)
    #             stats_label_text += f"{font_family}"
    #
    #         self.dimensions_label.setText(stats_label_text)

    def set_selection_size(self, num_selected: int):
        match num_selected:
            case 0:
                # File path label
                self.file_path_label.setText(f"<i>{Translations['preview.no_selection']}</i>")
                self.file_path_label.set_file_path(Path())
                self.file_path_label.setCursor(Qt.CursorShape.ArrowCursor)
                self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Properties
                self.date_created_label.setHidden(True)
                self.date_modified_label.setHidden(True)
                self.properties.setHidden(True)
            case 1:
                # File path label
                self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                self.file_path_label.setCursor(Qt.CursorShape.PointingHandCursor)

                # Properties
                self.date_created_label.setHidden(False)
                self.date_modified_label.setHidden(False)
                self.properties.setHidden(False)
            case _ if num_selected > 1:
                # File path label
                self.file_path_label.setText(
                    Translations.format("preview.multiple_selection", count=num_selected)
                )
                self.file_path_label.set_file_path(Path())
                self.file_path_label.setCursor(Qt.CursorShape.ArrowCursor)
                self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Properties
                self.date_created_label.setHidden(True)
                self.date_modified_label.setHidden(True)
                self.properties.setHidden(True)
