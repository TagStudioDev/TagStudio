import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from tagstudio.core.constants import VERSION
from tagstudio.core.ts_core import TagStudioCore
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.models.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.translations import Translations

logger = structlog.get_logger(__name__)


class OutOfDateMessageBox(QMessageBox):
    """A warning dialog for if the TagStudio is not running under the latest release version."""

    def __init__(self):
        super().__init__()

        title = Translations.format("version_modal.title")
        self.setWindowTitle(title)
        self.setIcon(QMessageBox.Icon.Warning)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.setStandardButtons(
            QMessageBox.StandardButton.Ignore | QMessageBox.StandardButton.Cancel
        )
        self.setDefaultButton(QMessageBox.StandardButton.Ignore)
        # Enables the cancel button but hides it to allow for click X to close dialog
        self.button(QMessageBox.StandardButton.Cancel).hide()

        red = get_ui_color(ColorType.PRIMARY, UiColor.RED)
        green = get_ui_color(ColorType.PRIMARY, UiColor.GREEN)
        latest_release_version = unwrap(TagStudioCore.get_most_recent_release_version())
        status = Translations.format(
            "version_modal.status",
            installed_version=f"<span style='color:{red}'>{VERSION}</span>",
            latest_release_version=f"<span style='color:{green}'>{latest_release_version}</span>",
        )
        self.setText(f"{Translations['version_modal.description']}<br><br>{status}")
