# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import typing
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QUrl,
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSlider, QVBoxLayout, QWidget

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

class AudioPlayer(QWidget):
    """A basic audio player widget.

    This widget is enabled if the selected
    file type is found in the AUDIO_TYPES list.
    """

    def __init__(self, driver: "QtDriver") -> None:
        super().__init__()
        self.driver = driver
        self.filepath: Path | None = None
        self.base_size: tuple[int, int] = (266, 75)

        self.setMinimumSize(*self.base_size)
        self.setMaximumSize(*self.base_size)

        # Set up the audio player
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(
            QAudioOutput(QMediaDevices().defaultAudioOutput(), self.player)
        )
        self.player.positionChanged.connect(self.position_changed)
        self.player.mediaStatusChanged.connect(self.media_status_changed)

        # widgets
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.setSpacing(6)

        self.pslider = QSlider(self)
        self.pslider.setMinimumWidth(266)
        self.pslider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.pslider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.pslider.setSingleStep(1)
        self.pslider.setOrientation(Qt.Orientation.Horizontal)

        self.ps_down = False
        self.pslider.sliderPressed.connect(self.slider_pressed)
        self.pslider.sliderReleased.connect(self.slider_released)

        self.base_layout.addWidget(self.pslider)

        # media buttons
        media_btns_layout = QHBoxLayout()

        self.media_play_btn = QPushButton("Play", self)
        self.media_play_btn.clicked.connect(self.play_clicked)
        self.media_play_btn.hide()

        self.media_pause_btn = QPushButton("Pause", self)
        self.media_pause_btn.clicked.connect(self.pause_clicked)

        self.media_mute_btn = QPushButton("Mute", self)
        self.media_mute_btn.clicked.connect(self.mute_clicked)

        self.media_unmute_btn = QPushButton("Unmute", self)
        self.media_unmute_btn.clicked.connect(self.unmute_clicked)
        self.media_unmute_btn.hide()

        # load svg files
        pix_map = QPixmap()
        if pix_map.loadFromData(self.driver.rm.play_icon):
            self.media_play_btn.setIcon(QIcon(pix_map))
        else:
            logging.error("failed to load play_icon svg")
        if pix_map.loadFromData(self.driver.rm.pause_icon):
            self.media_pause_btn.setIcon(QIcon(pix_map))
        else:
            logging.error("failed to load pause_icon svg")
        if pix_map.loadFromData(self.driver.rm.volume_mute_icon):
            self.media_mute_btn.setIcon(QIcon(pix_map))
        else:
            logging.error("failed to load volume_mute_icon svg")
        if pix_map.loadFromData(self.driver.rm.volume_icon):
            self.media_unmute_btn.setIcon(QIcon(pix_map))
        else:
            logging.error("failed to load volume_icon svg")

        media_btns_layout.addWidget(self.media_play_btn)
        media_btns_layout.addWidget(self.media_pause_btn)
        media_btns_layout.addWidget(self.media_mute_btn)
        media_btns_layout.addWidget(self.media_unmute_btn)
        self.base_layout.addLayout(media_btns_layout)

    def pause_clicked(self):
        self.media_pause_btn.hide()
        self.player.pause()
        self.media_play_btn.show()

    def play_clicked(self):
        # replay because we've reached the end of the track
        if self.pslider.value() == self.player.duration():
            self.player.setPosition(0)
            
        self.media_play_btn.hide()
        self.player.play()
        self.media_pause_btn.show()

    def mute_clicked(self):
        self.media_mute_btn.hide()
        self.player.audioOutput().setMuted(True)
        self.media_unmute_btn.show()

    def unmute_clicked(self):
        self.media_unmute_btn.hide()
        self.player.audioOutput().setMuted(False) 
        self.media_mute_btn.show()

    def slider_pressed(self):
        self.ps_down = True

    def slider_released(self):
        self.ps_down = False
        was_playing = self.player.isPlaying()
        self.player.setPosition(self.pslider.value())
        
        # Setting position causes the player to start playing again.
        # We should reset back to initial state.
        if not was_playing:
            self.player.pause()
            self.media_pause_btn.hide()
            self.media_play_btn.show()

    def position_changed(self, position: int) -> None:
        # user hasn't released the slider yet
        if self.ps_down:
            return

        self.pslider.setValue(position)
        if self.player.duration() == position: 
            self.player.pause()
            self.media_pause_btn.hide()
            self.media_play_btn.show()

    def close(self, *args, **kwargs) -> bool:
        self.player.stop()
        return super().close(*args, **kwargs)

    def load_file(self, filepath: Path) -> None:
        """Set the source of the QMediaPlayer and play."""
        self.filepath = filepath
        self.player.stop()
        self.player.setSource(QUrl().fromLocalFile(self.filepath))
        self.player.play()

    def stop(self) -> None:
        """Clear the filepath and stop the player."""
        self.filepath = None
        self.player.stop()

    def media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        # We can only set the slider duration once we know the size of the media
        if status == QMediaPlayer.MediaStatus.LoadedMedia and self.filepath is not None:
            self.pslider.setMinimum(0)
            self.pslider.setMaximum(self.player.duration())
