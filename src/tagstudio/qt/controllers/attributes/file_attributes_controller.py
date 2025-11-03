from pathlib import Path
import typing

from PySide6.QtGui import Qt
import structlog

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.models.preview_panel.attributes.file_attributes_model import FileAttributesModel, FilePropertyType
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.preview_panel.attributes.file_attributes_view import FileAttributesView
from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


logger = structlog.get_logger(__name__)


class FileAttributes(FileAttributesView):
    """A widget displaying a list of a file's attributes."""

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__(library, driver)

        self.model = FileAttributesModel()

    def update_file_property(self, property_type: FilePropertyType, **kwargs) -> None:
        """Update a property of the file."""
        logger.debug("[FileAttributes] Updating file property", type=property_type, **kwargs)

        if property_type not in self.model.get_properties():
            new_property_widget: FilePropertyWidget = property_type.widget_class()
            new_property_widget.set_value(**kwargs)

            self.model.add_property(property_type, new_property_widget)
            self.properties_layout.addWidget(new_property_widget)
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