from pathlib import Path

from PIL import ImageFont

from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget


class FontFamilyPropertyWidget(FilePropertyWidget):
    """A widget representing a file's font family."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("font_family_property")

    def set_value(self, **kwargs) -> None:
        file_path = kwargs.get("file_path", Path())

        font = ImageFont.truetype(file_path)
        font_family = font.getname()[0]
        font_style = font.getname()[1]

        self.setText(f"{font_family} ({font_style})")