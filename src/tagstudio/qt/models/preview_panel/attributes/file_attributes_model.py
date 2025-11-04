from enum import Enum

from PySide6.QtCore import QAbstractItemModel, Signal
import structlog

from tagstudio.qt.views.preview_panel.attributes.dimension_property_widget import (
    DimensionPropertyWidget,
)
from tagstudio.qt.views.preview_panel.attributes.duration_property_widget import (
    DurationPropertyWidget,
)
from tagstudio.qt.views.preview_panel.attributes.extension_and_size_property_widget import ExtensionAndSizePropertyWidget
from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget


logger = structlog.get_logger(__name__)


class FilePropertyType(Enum):
    EXTENSION_AND_SIZE = "extension_and_size", ExtensionAndSizePropertyWidget
    DIMENSIONS = "dimensions", DimensionPropertyWidget
    DURATION = "duration", DurationPropertyWidget

    def __init__(self, name: str, widget_class: type[FilePropertyWidget]):
        self.__name = name
        self.widget_class = widget_class


class FileAttributesModel(QAbstractItemModel):
    properties_changed: Signal = Signal(dict)

    def __init__(self):
        super().__init__()

        self.__property_widgets: dict[FilePropertyType, FilePropertyWidget] = {}

    def get_properties(self) -> dict[FilePropertyType, FilePropertyWidget]:
        return dict(
            sorted(
                self.__property_widgets.items(),
                key=lambda item: list(FilePropertyType.__members__.values()).index(item[0]),
            )
        )

    def get_property_index(self, property_type: FilePropertyType) -> int:
        for index, key in enumerate(self.get_properties()):
            if property_type == key: return index

        return -1

    def get_property(self, property_type: FilePropertyType) -> FilePropertyWidget | None:
        if property_type in self.__property_widgets:
            return self.__property_widgets[property_type]

        return None

    def add_property(self, property_type: FilePropertyType, widget: FilePropertyWidget) -> None:
        if property_type not in self.__property_widgets:
            self.__property_widgets[property_type] = widget

        self.properties_changed.emit(self.get_properties())

    def set_property(self, property_type: FilePropertyType, widget: FilePropertyWidget) -> None:
        if property_type not in self.__property_widgets:
            self.__property_widgets[property_type] = widget

        self.properties_changed.emit(self.get_properties())

    def delete_property(self, property_type: FilePropertyType) -> None:
        self.__property_widgets.pop(property_type, None)

    def delete_properties(self) -> None:
        self.__property_widgets.clear()
