from pathlib import Path

import structlog
from PIL import ImageFont

from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget

logger = structlog.get_logger(__name__)


class FontFamilyPropertyWidget(FilePropertyWidget):
    """A widget representing a file's font family."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("font_family_property")

    def set_value(self, **kwargs) -> bool:
        file_path = kwargs.get("file_path", Path())

        try:
            font = ImageFont.truetype(file_path)
            font_family = font.getname()[0]
            font_style = font.getname()[1]

            self.setText(f"{font_family} ({font_style})")
            return True
        except (FileNotFoundError, OSError) as error:
            logger.error(
                "[FontFamilyPropertyWidget] Could not process font family",
                file_path=file_path,
                error=error,
            )
            return False
