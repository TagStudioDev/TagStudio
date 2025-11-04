import os
import platform
import typing
from datetime import datetime as dt
from pathlib import Path

import structlog
from PySide6.QtGui import Qt

from tagstudio.core.enums import ShowFilepathOption
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaCategories
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.models.preview_panel.attributes.file_attributes_model import (
    FileAttributesModel,
    FilePropertyType,
)
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.preview_panel.attributes.file_attributes_view import FileAttributesView
from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


logger = structlog.get_logger(__name__)


class FileAttributes(FileAttributesView):
    """A widget displaying a list of a file's attributes."""

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()
        self.library = library
        self.driver = driver

        self.model = FileAttributesModel()

    def update_file_path(self, file_path: Path) -> None:
        self.file_path_label.set_file_path(file_path)

        # Update path-based properties
        self.update_file_property(FilePropertyType.EXTENSION_AND_SIZE, file_path=file_path)

        if MediaCategories.is_ext_in_category(
            file_path.suffix.lower(), MediaCategories.FONT_TYPES, mime_fallback=True
        ):
            self.update_file_property(
                FilePropertyType.FONT_FAMILY, file_path=file_path
            )

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
        path_separator: str = f"<a style='color: #777777'><b>{os.path.sep}</b></a>"  # Gray

        path_parts: list[str] = list(display_path.parts)
        path_parts[-1] = f"<br><b>{path_parts[-1]}</b>"

        path_string: str = path_separator.join(path_parts)
        self.file_path_label.setText(path_string)

    def update_date_label(self, file_path: Path | None = None) -> None:
        """Update the "Date Created" and "Date Modified" file property labels."""
        date_created: str | None = None
        date_modified: str | None = None
        if file_path and file_path.is_file():
            # Date created
            created_timestamp: dt
            if platform.system() == "Windows" or platform.system() == "Darwin":
                created_timestamp = dt.fromtimestamp(file_path.stat().st_birthtime)  # type: ignore[attr-defined, unused-ignore]
            else:
                created_timestamp = dt.fromtimestamp(file_path.stat().st_ctime)

            date_created = self.driver.settings.format_datetime(created_timestamp)

            # Date modified
            modified_timestamp: dt = dt.fromtimestamp(file_path.stat().st_mtime)
            date_modified = self.driver.settings.format_datetime(modified_timestamp)
        elif file_path:
            date_created = "<i>N/A</i>"
            date_modified = "<i>N/A</i>"

        if date_created is not None:
            self.date_created_label.setText(
                f"<b>{Translations['file.date_created']}:</b> {date_created}"
            )
            self.date_created_label.setHidden(False)
        else:
            self.date_created_label.setHidden(True)

        if date_modified is not None:
            self.date_modified_label.setText(
                f"<b>{Translations['file.date_modified']}:</b> {date_modified}"
            )
            self.date_modified_label.setHidden(False)
        else:
            self.date_modified_label.setHidden(True)

    def update_file_property(self, property_type: FilePropertyType, **kwargs) -> None:
        """Update a property of the file."""
        logger.debug("[FileAttributes] Updating file property", type=property_type, **kwargs)

        if property_type not in self.model.get_properties():
            new_property_widget: FilePropertyWidget = property_type.widget_class()
            new_property_widget.set_value(**kwargs)

            self.model.add_property(property_type, new_property_widget)
            self.properties_layout.insertWidget(
                self.model.get_property_index(property_type),
                new_property_widget
            )
        else:
            property_widget: FilePropertyWidget | None = self.model.get_property(property_type)
            if property_widget:
                property_widget.set_value(**kwargs)

                self.model.set_property(property_type, property_widget)
                property_widget.show()

    def clear_file_properties(self) -> None:
        """Clears the existing file properties."""
        logger.debug("[FileAttributes] Clearing file properties")

        for property_widget in self.model.get_properties().values():
            property_widget.hide()

        self.model.delete_properties()

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
