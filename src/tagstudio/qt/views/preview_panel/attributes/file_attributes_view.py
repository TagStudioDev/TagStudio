# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from dataclasses import dataclass

import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from tagstudio.core.enums import Theme
from tagstudio.qt.utils.file_opener import FileOpenerLabel

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

    def __init__(self):
        super().__init__()

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
    #             except (FileNotFoundError, OSError) as e:
    #                 logger.error(
    #                     "[FileAttributes] Could not process file stats", filepath=filepath, error=e
    #                 )
    #
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
    #         self.dimensions_label.setText(stats_label_text)
