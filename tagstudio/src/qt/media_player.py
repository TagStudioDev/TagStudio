# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer


class MediaPlayer:
    def __init__(self):
        self.filepath: Path | None = None
        self.player = QMediaPlayer()
        self.player.setAudioOutput(QAudioOutput(QMediaDevices().defaultAudioOutput(), self.player))

        # Used to keep track of play state.
        # It would be nice if we could use QMediaPlayer.PlaybackState,
        # but this will always show StoppedState when changing
        # tracks. Therefore, we wouldn't know if the previous
        # state was paused or playing
        self.is_paused = False

    def toggle_pause(self) -> None:
        """Toggle the pause state of the media."""
        if self.player.isPlaying():
            self.player.pause()
            self.is_paused = True
        else:
            self.player.play()
            self.is_paused = False

    def toggle_mute(self) -> None:
        """Toggle the mute state of the media."""
        if self.player.audioOutput().isMuted():
            self.player.audioOutput().setMuted(False)
        else:
            self.player.audioOutput().setMuted(True)

    def stop(self) -> None:
        """Clear the filepath and stop the player."""
        self.filepath = None
        self.player.stop()

    def play(self, filepath: Path) -> None:
        """Set the source of the QMediaPlayer and play."""
        self.filepath = filepath
        if not self.is_paused:
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(self.filepath))
            self.player.play()
        else:
            self.player.setSource(QUrl.fromLocalFile(self.filepath))
