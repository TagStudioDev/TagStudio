# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import typing
from pathlib import Path
from time import gmtime
from typing import Any

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QWidget,
)

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class MediaPlayer(QWidget):
    """A basic media player widget.

    Gives a basic control set to manage media playback.
    """

    def __init__(self, driver: "QtDriver") -> None:
        super().__init__()
        self.driver = driver

        self.setFixedHeight(50)

        self.filepath: Path | None = None
        self.player = QMediaPlayer()
        self.player.setAudioOutput(QAudioOutput(QMediaDevices().defaultAudioOutput(), self.player))

        # Used to keep track of play state.
        # It would be nice if we could use QMediaPlayer.PlaybackState,
        # but this will always show StoppedState when changing
        # tracks. Therefore, we wouldn't know if the previous
        # state was paused or playing
        self.is_paused = False

        # Subscribe to player events from MediaPlayer
        self.player.positionChanged.connect(self.player_position_changed)
        self.player.mediaStatusChanged.connect(self.media_status_changed)
        self.player.playingChanged.connect(self.playing_changed)
        self.player.audioOutput().mutedChanged.connect(self.muted_changed)

        # Media controls
        self.base_layout = QGridLayout(self)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.setSpacing(0)

        self.pslider = QSlider(self)
        self.pslider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.pslider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.pslider.setSingleStep(1)
        self.pslider.setOrientation(Qt.Orientation.Horizontal)

        self.pslider.sliderReleased.connect(self.slider_released)
        self.pslider.valueChanged.connect(self.slider_value_changed)

        self.media_btns_layout = QHBoxLayout()

        policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.play_pause = QPushButton("", self)
        self.play_pause.setFlat(True)
        self.play_pause.setSizePolicy(policy)
        self.play_pause.clicked.connect(self.toggle_pause)

        self.load_play_pause_icon(playing=False)

        self.media_btns_layout.addWidget(self.play_pause)

        self.mute = QPushButton("", self)
        self.mute.setFlat(True)
        self.mute.setSizePolicy(policy)
        self.mute.clicked.connect(self.toggle_mute)

        self.load_mute_unmute_icon(muted=False)

        self.media_btns_layout.addWidget(self.mute)

        self.position_label = QLabel("0:00")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.base_layout.addWidget(self.pslider, 0, 0, 1, 2)
        self.base_layout.addLayout(self.media_btns_layout, 1, 0)
        self.base_layout.addWidget(self.position_label, 1, 1)

    def format_time(self, ms: int) -> str:
        """Format the given time.

        Formats the given time in ms to a nicer format.

        Args:
            ms: Time in ms

        Returns:
            A formatted time:

            "1:43"

            The formatted time will only include the hour if
            the provided time is at least 60 minutes.
        """
        time = gmtime(ms / 1000)
        return (
            f"{time.tm_hour}:{time.tm_min}:{time.tm_sec:02}"
            if time.tm_hour > 0
            else f"{time.tm_min}:{time.tm_sec:02}"
        )

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

    def playing_changed(self, playing: bool) -> None:
        self.load_play_pause_icon(playing)

    def muted_changed(self, muted: bool) -> None:
        self.load_mute_unmute_icon(muted)

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

    def load_play_pause_icon(self, playing: bool) -> None:
        icon = self.driver.rm.pause_icon if playing else self.driver.rm.play_icon
        self.set_icon(self.play_pause, icon)

    def load_mute_unmute_icon(self, muted: bool) -> None:
        icon = self.driver.rm.volume_mute_icon if muted else self.driver.rm.volume_icon
        self.set_icon(self.mute, icon)

    def set_icon(self, btn: QPushButton, icon: Any) -> None:
        pix_map = QPixmap()
        if pix_map.loadFromData(icon):
            btn.setIcon(QIcon(pix_map))
        else:
            logging.error("failed to load svg file")

    def slider_value_changed(self, value: int) -> None:
        current = self.format_time(value)
        duration = self.format_time(self.player.duration())
        self.position_label.setText(f"{current} / {duration}")

    def slider_released(self) -> None:
        was_playing = self.player.isPlaying()
        self.player.setPosition(self.pslider.value())

        # Setting position causes the player to start playing again.
        # We should reset back to initial state.
        if not was_playing:
            self.player.pause()

    def player_position_changed(self, position: int) -> None:
        if not self.pslider.isSliderDown():
            # User isn't using the slider, so update position in widgets.
            self.pslider.setValue(position)
            current = self.format_time(self.player.position())
            duration = self.format_time(self.player.duration())
            self.position_label.setText(f"{current} / {duration}")

        if self.player.duration() == position:
            self.player.pause()
            self.player.setPosition(0)

    def media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        # We can only set the slider duration once we know the size of the media
        if status == QMediaPlayer.MediaStatus.LoadedMedia and self.filepath is not None:
            self.pslider.setMinimum(0)
            self.pslider.setMaximum(self.player.duration())

            current = self.format_time(self.player.position())
            duration = self.format_time(self.player.duration())
            self.position_label.setText(f"{current} / {duration}")
