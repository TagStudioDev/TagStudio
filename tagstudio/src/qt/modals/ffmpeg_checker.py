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
    warning_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[3] / "resources/qt/images/thumb_warning.png")
    ).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
    warning_icon_128.load()

    help_url = "https://github.com/TagStudioDev/TagStudio/blob/Alpha-v9.4/doc/utilities/ffmpeg.md"

    def __init__(self):
        super().__init__()

        #self.warning_icon = QPixmap.fromImage(ImageQt.ImageQt(self.warning_icon_128))
        #self.setIconPixmap(self.warning_icon)
        self.setIcon(QMessageBox.Warning)

        self.setText("Warning: Could not find FFmpeg installation")
        self.setStandardButtons(QMessageBox.Help | QMessageBox.Ignore)
        self.setDefaultButton(QMessageBox.Ignore)

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle("Warning: Missing dependency")

        self.ffmpeg_installed = False
        self.ffprobe_installed = False

    def installed(self):
        """Checks if both FFmpeg and FFprobe are installed"""
        if which("ffmpeg"):
            self.ffmpeg_installed = True
            logging.info(f"FFmpeg found!")
        if which("ffprobe"):
            self.ffprobe_installed = True
            logging.info(f"FFprobe found!")
        return self.ffmpeg_installed and self.ffprobe_installed

    def show_warning(self):
        if not self.ffmpeg_installed:
            self.setText("Warning: Could not find FFmpeg installation")
            self.setInformativeText("FFmpeg is required for video/audio thumbnails and playback")
        elif not self.ffprobe_installed:
            # If ffmpeg is installed but not ffprobe
            self.setText("Warning: Could not find FFprobe installation")
            self.setInformativeText("FFprobe is required for video/audio thumbnails and playback")

        selection = self.exec()
        if selection == QMessageBox.Help:
            QDesktopServices.openUrl(QUrl(self.help_url))
