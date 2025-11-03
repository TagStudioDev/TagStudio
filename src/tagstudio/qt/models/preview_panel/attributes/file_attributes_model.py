from enum import Enum

from PySide6.QtCore import QAbstractItemModel, Signal

from tagstudio.qt.views.preview_panel.attributes.dimension_property_widget import (
    DimensionPropertyWidget,
)
from tagstudio.qt.views.preview_panel.attributes.duration_property_widget import (
    DurationPropertyWidget,
)
from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget


class FilePropertyType(Enum):
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
        return self.__property_widgets

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
