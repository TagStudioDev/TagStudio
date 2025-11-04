from pathlib import Path

from humanfriendly import format_size
import structlog

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.models.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.preview_panel.attributes.file_property_widget import FilePropertyWidget
from tagstudio.core.library.ignore import Ignore


logger = structlog.get_logger(__name__)


class ExtensionAndSizePropertyWidget(FilePropertyWidget):
    """A widget representing a file's extension and size."""

    red = get_ui_color(ColorType.PRIMARY, UiColor.RED)
    orange = get_ui_color(ColorType.PRIMARY, UiColor.ORANGE)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("extension_and_size_property")

    def set_value(self, **kwargs) -> bool:
        file_path = kwargs.get("file_path", Path())
        library_dir: Path | None = kwargs.get("library_dir", None)

        try:
            components: list[str] = []

            # File extension
            extension: str = file_path.suffix.upper()[1:] or file_path.stem.upper()
            components.append(extension)

            # File size
            if file_path and file_path.is_file():
                file_size = file_path.stat().st_size
                if file_size and file_size > 0:
                    components.append(format_size(file_size))

            # Ignored
            if library_dir and Ignore.compiled_patterns and Ignore.compiled_patterns.match(
                file_path.relative_to(unwrap(library_dir))
            ):
                components.append(
                    f"<span style='color: {self.orange};'>{Translations['preview.ignored'].upper()}</span>"
                )

            # Unlinked
            if not file_path.exists():
                components.append(
                    f"<span style='color: {self.red};'>{Translations['preview.unlinked'].upper()}</span>"
                )

            self.setText("  •  ".join(components))
            return True
        except (FileNotFoundError, OSError) as error:
            logger.error(
                "[ExtensionAndSizePropertyWidget] Could not process file stats",
                file_path=file_path,
                error=error,
            )
            return False