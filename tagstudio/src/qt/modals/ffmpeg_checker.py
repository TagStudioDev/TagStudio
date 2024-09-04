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

        self.setIcon(QMessageBox.Warning)

        self.setText("Warning: Could not find FFmpeg installation")
        self.setStandardButtons(QMessageBox.Help | QMessageBox.Ignore)
        self.setDefaultButton(QMessageBox.Ignore)

        # Blocks other application interactions until resolved
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle("Warning: Missing dependency")

        self.ffmpeg_missing = True
        self.ffprobe_missing = True

    def installed(self):
        """Checks if both FFmpeg and FFprobe are installed and in the PATH."""
        # Same checker that ffmpeg-python uses
        if which("ffmpeg"):
            self.ffmpeg_missing = False
            logging.info(f"FFmpeg found!")
        if which("ffprobe"):
            self.ffprobe_missing = False
            logging.info(f"FFprobe found!")
        # Reverse from missing to installed
        return not (self.ffmpeg_missing or self.ffprobe_missing)

    def show_warning(self):
        """Displays the warning to the user and awaits respone."""
        missing = "FFmpeg"
        # If ffmpeg is installed but not ffprobe
        if self.ffprobe_missing and not self.ffmpeg_missing:
            missing = "FFprobe"

        self.setText(f"Warning: Could not find {missing} installation")
        self.setInformativeText(
            f"{missing} is required for multimedia thumbnails and playback"
        )
        # Shows the dialog
        selection = self.exec()

        # Selection will either be QMessageBox.Help or QMessageBox.Ignore
        if selection == QMessageBox.Help:
            QDesktopServices.openUrl(QUrl(self.help_url))
