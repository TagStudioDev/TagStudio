from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget


class DimensionPropertyWidget(FilePropertyWidget):
    """A widget representing a file's dimensions."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("dimensions_property")

    def set_value(self, **kwargs) -> None:
        width: int = kwargs.get("width", 0)
        height: int = kwargs.get("height", 0)

        self.setText(f"{width} x {height} px")
