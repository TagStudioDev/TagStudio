# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import typing
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QWidget,
)
from src.qt.media_player import MediaPlayer

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class AudioPlayer(QWidget, MediaPlayer):
    """A basic audio player widget.

    This widget is enabled if the selected
    file type is found in the AUDIO_TYPES list.
    """

    def __init__(self, driver: "QtDriver") -> None:
        super().__init__()
        self.driver = driver

        self.setFixedHeight(50)

        # Subscribe to player events from MediaPlayer
        self.player.positionChanged.connect(self.position_changed)
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

        self.position_label = QLabel("positionLabel")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.base_layout.addWidget(self.pslider, 0, 0, 1, 2)
        self.base_layout.addLayout(self.media_btns_layout, 1, 0)
        self.base_layout.addWidget(self.position_label, 1, 1)

    def load_play_pause_icon(self, playing: bool) -> None:
        icon = self.driver.rm.pause_icon if playing else self.driver.rm.play_icon
        self.set_icon(self.play_pause, icon)

    def load_mute_unmute_icon(self, muted: bool) -> None:
        icon = self.driver.rm.volume_icon if muted else self.driver.rm.volume_mute_icon
        self.set_icon(self.mute, icon)

    def set_icon(self, btn: QPushButton, icon: Any) -> None:
        pix_map = QPixmap()
        if pix_map.loadFromData(icon):
            btn.setIcon(QIcon(pix_map))
        else:
            logging.error("failed to load svg file")

    def format_time(self, time: int) -> str:
        """Format the given time.

        Formats the given time in ms to a nicer format.

        Args:
            time: Time in ms

        Returns:
            A formatted time:

            "1:43"

            The formatted time will only include the hour if
            the provided time is at least 60 minutes.
        """
        pretty_time = ""
        if time > (60 * 60 * 1000):
            pretty_time += f"{int(time / (60 * 60 * 1000)) % 24}:"

        if time > (60 * 1000):
            pretty_time += f"{int(time / (60 * 1000)) % 60}:"
        else:
            pretty_time += "0:"

        if time > 1000:
            pretty_time += f"{int(time / 1000) % 60:02d}"
        else:
            pretty_time += "00"

        return pretty_time

    def slider_released(self) -> None:
        was_playing = self.player.isPlaying()
        self.player.setPosition(self.pslider.value())

        # Setting position causes the player to start playing again.
        # We should reset back to initial state.
        if not was_playing:
            self.player.pause()

    def position_changed(self, position: int) -> None:
        # user hasn't released the slider yet
        if self.pslider.isSliderDown():
            return

        self.pslider.setValue(position)

        current = self.format_time(self.player.position())
        duration = self.format_time(self.player.duration())
        self.position_label.setText(f"{current} / {duration}")

        if self.player.duration() == position:
            self.player.pause()
            self.player.setPosition(0)

    def playing_changed(self, playing: bool) -> None:
        self.load_play_pause_icon(playing)

    def muted_changed(self, muted: bool) -> None:
        self.load_mute_unmute_icon(muted)

    def media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        # We can only set the slider duration once we know the size of the media
        if status == QMediaPlayer.MediaStatus.LoadedMedia and self.filepath is not None:
            self.pslider.setMinimum(0)
            self.pslider.setMaximum(self.player.duration())

            current = self.format_time(self.player.position())
            duration = self.format_time(self.player.duration())
            self.position_label.setText(f"{current} / {duration}")
