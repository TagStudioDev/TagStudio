import logging
import math
from pathlib import Path
import subprocess

from PIL import Image, ImageQt
from pydub.utils import which
from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtWidgets import QMessageBox


class FfmpegChecker(QMessageBox):
    """A warning dialog for if FFmpeg is missing."""

    help_url = "https://github.com/TagStudioDev/TagStudio/blob/Alpha-v9.4/doc/utilities/ffmpeg.md"

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Warning: Missing dependency")
        self.setText("Warning: Could not find FFmpeg installation")
        self.setIcon(QMessageBox.Warning)
        # Blocks other application interactions until resolved
        self.setWindowModality(Qt.ApplicationModal)

        self.setStandardButtons(
            QMessageBox.Help | QMessageBox.Ignore | QMessageBox.Cancel
        )
        self.setDefaultButton(QMessageBox.Ignore)
        # Enables the cancel button but hides it to allow for click X to close dialog
        self.button(QMessageBox.Cancel).hide()

        self.ffmpeg = False
        self.ffprobe = False

    def installed(self):
        """Checks if both FFmpeg and FFprobe are installed and in the PATH."""
        # Same checker that ffmpeg-python uses
        if which("ffmpeg"):
            self.ffmpeg = True
        if which("ffprobe"):
            self.ffprobe = True

        logging.info(
            f"[FFmpegChecker] FFmpeg found: {self.ffmpeg}, FFprobe found: {self.ffprobe}"
        )
        return self.ffmpeg and self.ffprobe

    def show_warning(self):
        """Displays the warning to the user and awaits respone."""
        missing = "FFmpeg"
        # If ffmpeg is installed but not ffprobe
        if not self.ffprobe and self.ffmpeg:
            missing = "FFprobe"

        self.setText(f"Warning: Could not find {missing} installation")
        self.setInformativeText(
            f"{missing} is required for multimedia thumbnails and playback"
        )
        # Shows the dialog
        selection = self.exec()

        # Selection will either be QMessageBox.Help or (QMessageBox.Ignore | QMessageBox.Cancel) which can be ignored
        if selection == QMessageBox.Help:
            QDesktopServices.openUrl(QUrl(self.help_url))
