from pathlib import Path

from humanfriendly import format_size

from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget


class ExtensionAndSizePropertyWidget(FilePropertyWidget):
    """A widget representing a file's extension and size."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("extension_and_size_property")

    def set_value(self, **kwargs) -> None:
        file_path = kwargs.get("file_path", Path())

        extension: str = file_path.suffix.upper()[1:] or file_path.stem.upper()
        file_size: int = 0

        if file_path and file_path.is_file():
            file_size = file_path.stat().st_size

        if file_size > 0:
            self.setText(f"{extension}  •  {format_size(file_size)}")
        else:
            self.setText(extension)