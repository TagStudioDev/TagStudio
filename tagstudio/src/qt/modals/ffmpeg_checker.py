import contextlib
import subprocess
from shutil import which

import structlog
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox
from src.qt.helpers.vendored.ffmpeg import FFMPEG_CMD, FFPROBE_CMD

logger = structlog.get_logger(__name__)


class FfmpegChecker(QMessageBox):
    """A warning dialog for if FFmpeg is missing."""

    HELP_URL = "https://docs.tagstud.io/help/ffmpeg/"

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Warning: Missing dependency")
        self.setText("Warning: Could not find FFmpeg installation")
        self.setIcon(QMessageBox.Icon.Warning)
        # Blocks other application interactions until resolved
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.setStandardButtons(
            QMessageBox.StandardButton.Help
            | QMessageBox.StandardButton.Ignore
            | QMessageBox.StandardButton.Cancel
        )
        self.setDefaultButton(QMessageBox.StandardButton.Ignore)
        # Enables the cancel button but hides it to allow for click X to close dialog
        self.button(QMessageBox.StandardButton.Cancel).hide()

        self.ffmpeg = False
        self.ffprobe = False

    def installed(self):
        """Checks if both FFmpeg and FFprobe are installed and in the PATH."""
        if which(FFMPEG_CMD):
            self.ffmpeg = True
        if which(FFPROBE_CMD):
            self.ffprobe = True

        logger.info("FFmpeg found: {self.ffmpeg}, FFprobe found: {self.ffprobe}")
        return self.ffmpeg and self.ffprobe

    def version(self):
        """Checks the version of ffprobe and ffmpeg and returns None if they dont exist."""
        version: dict[str, str | None] = {"ffprobe": None, "ffmpeg": None}
        self.installed()
        if self.ffprobe:
            ret = subprocess.run(
                [FFPROBE_CMD, "-show_program_version"], shell=False, capture_output=True, text=True
            )
            if ret.returncode == 0:
                with contextlib.suppress(Exception):
                    version["ffprobe"] = ret.stdout.split("\n")[1].replace("-", "=").split("=")[1]
        if self.ffmpeg:
            ret = subprocess.run(
                [FFMPEG_CMD, "-version"], shell=False, capture_output=True, text=True
            )
            if ret.returncode == 0:
                with contextlib.suppress(Exception):
                    version["ffmpeg"] = ret.stdout.replace("-", " ").split(" ")[2]
        return version

    def show_warning(self):
        """Displays the warning to the user and awaits response."""
        missing = "FFmpeg"
        # If ffmpeg is installed but not ffprobe
        if not self.ffprobe and self.ffmpeg:
            missing = "FFprobe"

        self.setText(f"Warning: Could not find {missing} installation")
        self.setInformativeText(f"{missing} is required for multimedia thumbnails and playback")
        # Shows the dialog
        selection = self.exec()

        # Selection will either be QMessageBox.Help or (QMessageBox.Ignore | QMessageBox.Cancel)
        if selection == QMessageBox.StandardButton.Help:
            QDesktopServices.openUrl(QUrl(self.HELP_URL))
