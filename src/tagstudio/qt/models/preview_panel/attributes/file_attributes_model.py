from enum import Enum

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
