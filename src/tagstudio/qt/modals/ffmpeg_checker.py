from shutil import which

import structlog
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from tagstudio.core.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.helpers.vendored.ffmpeg import FFMPEG_CMD, FFPROBE_CMD
from tagstudio.qt.translations import Translations

logger = structlog.get_logger(__name__)


class FfmpegChecker(QMessageBox):
    """A warning dialog for if FFmpeg is missing."""

    HELP_URL = "https://docs.tagstud.io/help/ffmpeg/"

    def __init__(self):
        super().__init__()

        ffmpeg = "FFmpeg"
        ffprobe = "FFprobe"
        title = Translations.format("dependency.missing.title", dependency=ffmpeg)
        self.setWindowTitle(title)
        self.setIcon(QMessageBox.Icon.Warning)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.setStandardButtons(
            QMessageBox.StandardButton.Help
            | QMessageBox.StandardButton.Ignore
            | QMessageBox.StandardButton.Cancel
        )
        self.setDefaultButton(QMessageBox.StandardButton.Ignore)
        # Enables the cancel button but hides it to allow for click X to close dialog
        self.button(QMessageBox.StandardButton.Cancel).hide()
        self.button(QMessageBox.StandardButton.Help).clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(self.HELP_URL))
        )

        red = get_ui_color(ColorType.PRIMARY, UiColor.RED)
        green = get_ui_color(ColorType.PRIMARY, UiColor.GREEN)
        missing = f"<span style='color:{red}'>{Translations['generic.missing']}</span>"
        found = f"<span style='color:{green}'>{Translations['about.module.found']}</span>"
        status = Translations.format(
            "ffmpeg.missing.status",
            ffmpeg=ffmpeg,
            ffmpeg_status=found if which(FFMPEG_CMD) else missing,
            ffprobe=ffprobe,
            ffprobe_status=found if which(FFPROBE_CMD) else missing,
        )
        self.setText(f"{Translations['ffmpeg.missing.description']}<br><br>{status}")
