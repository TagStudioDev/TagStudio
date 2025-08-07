# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing
from pathlib import Path
from time import gmtime
from typing import override

import structlog
from PIL import Image, ImageDraw
from PySide6.QtCore import QEvent, QObject, QRectF, QSize, Qt, QUrl, QVariantAnimation
from PySide6.QtGui import (
    QAction,
    QBitmap,
    QBrush,
    QColor,
    QLinearGradient,
    QMouseEvent,
    QPen,
    QRegion,
    QResizeEvent,
)
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from tagstudio.qt.helpers.qslider_wrapper import QClickSlider
from tagstudio.qt.translations import Translations

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class MediaPlayer(QGraphicsView):
    """A basic media player widget.

    Gives a basic control set to manage media playback.
    """

    video_preview: "VideoPreview | None" = None

    def __init__(self, driver: "QtDriver") -> None:
        super().__init__()
        self.driver = driver

        slider_style = """
            QSlider {
                background: transparent;
                margin-right: 6px;
            }

            QSlider::add-page:horizontal {
                background: #65000000;
                border-radius: 3px;
                border-style: solid;
                border-width: 1px;
                border-color: #65444444;
            }

            QSlider::sub-page:horizontal {
                background: #88FFFFFF;
                border-radius: 3px;
            }

            QSlider::groove:horizontal {
                background: transparent;
                height: 6px;
            }

            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 12px;
                margin: -3px 0;
                border-radius: 6px;
            }
        """

        fixed_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        retain_policy = QSizePolicy()
        retain_policy.setRetainSizeWhenHidden(True)
        self.filepath: Path | None = None

        # Graphics Scene
        self.installEventFilter(self)
        self.setScene(QGraphicsScene(self))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QGraphicsView {
               background: transparent;
               border: none;
            }
        """)
        self.setObjectName("mediaPlayer")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.video_preview = VideoPreview()
        self.video_preview.setAcceptHoverEvents(True)
        self.video_preview.setAcceptedMouseButtons(Qt.MouseButton.RightButton)
        self.video_preview.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.video_preview.installEventFilter(self)

        self.animation = QVariantAnimation(self)
        self.animation.valueChanged.connect(lambda value: self.set_tint_opacity(value))
        self.tint = self.scene().addRect(
            0,
            0,
            self.size().width(),
            12,
            QPen(QColor(0, 0, 0, 0)),
            QBrush(QColor(0, 0, 0, 0)),
        )

        # Player
        self.player = QMediaPlayer()
        self.player.setAudioOutput(QAudioOutput(QMediaDevices().defaultAudioOutput(), self.player))
        self.is_paused = (
            False  # Q MediaPlayer.PlaybackState shows StoppedState when changing tracks
        )

        self.player.positionChanged.connect(self.player_position_changed)
        self.player.mediaStatusChanged.connect(self.media_status_changed)
        self.player.playingChanged.connect(self.playing_changed)
        self.player.hasVideoChanged.connect(self.has_video_changed)
        self.player.audioOutput().mutedChanged.connect(self.muted_changed)

        # Media Controls
        self.controls = QWidget()
        self.controls.setObjectName("controls")
        root_layout = QVBoxLayout(self.controls)
        root_layout.setContentsMargins(6, 0, 6, 0)
        root_layout.setSpacing(6)
        self.controls.setStyleSheet("background: transparent;")
        self.controls.setMinimumHeight(48)

        self.timeline_slider = QClickSlider()
        self.timeline_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.timeline_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.timeline_slider.setSingleStep(1)
        self.timeline_slider.setOrientation(Qt.Orientation.Horizontal)
        self.timeline_slider.setStyleSheet(slider_style)
        self.timeline_slider.sliderReleased.connect(self.slider_released)
        self.timeline_slider.valueChanged.connect(self.slider_value_changed)
        self.timeline_slider.hide()
        self.timeline_slider.setFixedHeight(12)

        root_layout.addWidget(self.timeline_slider)
        root_layout.setAlignment(self.timeline_slider, Qt.AlignmentFlag.AlignBottom)

        self.sub_controls = QWidget()
        self.sub_controls.setMouseTracking(True)
        self.sub_controls.installEventFilter(self)
        sub_layout = QHBoxLayout(self.sub_controls)
        sub_layout.setContentsMargins(0, 0, 0, 6)
        self.sub_controls.setStyleSheet("background: transparent;")
        self.sub_controls.setMinimumHeight(16)

        self.play_pause = QSvgWidget()
        self.play_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_pause.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, on=True)
        self.play_pause.setMouseTracking(True)
        self.play_pause.installEventFilter(self)
        self.load_toggle_play_icon(playing=False)
        self.play_pause.resize(16, 16)
        self.play_pause.setSizePolicy(fixed_policy)
        self.play_pause.setStyleSheet("background: transparent;")
        self.play_pause.hide()

        sub_layout.addWidget(self.play_pause)
        sub_layout.setAlignment(self.play_pause, Qt.AlignmentFlag.AlignLeft)

        self.mute_unmute = QSvgWidget()
        self.mute_unmute.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_unmute.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, on=True)
        self.mute_unmute.setMouseTracking(True)
        self.mute_unmute.installEventFilter(self)
        self.load_mute_unmute_icon(muted=False)
        self.mute_unmute.resize(16, 16)
        self.mute_unmute.setSizePolicy(fixed_policy)
        self.mute_unmute.hide()

        sub_layout.addWidget(self.mute_unmute)
        sub_layout.setAlignment(self.mute_unmute, Qt.AlignmentFlag.AlignLeft)

        self.volume_slider = QClickSlider()
        self.volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.volume_slider.setValue(int(self.player.audioOutput().volume() * 100))
        self.volume_slider.valueChanged.connect(self.volume_slider_changed)
        self.volume_slider.setStyleSheet(slider_style)
        self.volume_slider.setSizePolicy(retain_policy)
        self.volume_slider.hide()
        self.volume_slider.setMinimumWidth(32)

        sub_layout.addWidget(self.volume_slider)
        sub_layout.setAlignment(self.volume_slider, Qt.AlignmentFlag.AlignLeft)
        sub_layout.addStretch()

        self.position_label = QLabel("0:00")
        self.position_label.setStyleSheet("color: white;")
        sub_layout.addWidget(self.position_label)
        root_layout.setAlignment(self.position_label, Qt.AlignmentFlag.AlignRight)
        self.position_label.hide()

        root_layout.addWidget(self.sub_controls)
        self.scene().addWidget(self.controls)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        autoplay_action = QAction(Translations["media_player.autoplay"], self)
        autoplay_action.setCheckable(True)
        self.addAction(autoplay_action)
        autoplay_action.setChecked(self.driver.settings.autoplay)
        autoplay_action.triggered.connect(lambda: self.toggle_autoplay())
        self.autoplay = autoplay_action

        loop_action = QAction(Translations["media_player.loop"], self)
        loop_action.setCheckable(True)
        self.addAction(loop_action)
        loop_action.setChecked(self.driver.settings.loop)
        loop_action.triggered.connect(lambda: self.toggle_loop())
        self.loop = loop_action
        self.toggle_loop()

        self.player.audioOutput().setMuted(True)

    def set_video_output(self, video: QGraphicsVideoItem):
        self.player.setVideoOutput(video)

    def toggle_autoplay(self) -> None:
        """Toggle the autoplay state of the video."""
        self.driver.settings.autoplay = self.autoplay.isChecked()
        self.driver.settings.save()

    def toggle_loop(self) -> None:
        self.driver.settings.loop = self.loop.isChecked()
        self.driver.settings.save()
        self.player.setLoops(-1 if self.driver.settings.loop else 1)

    def apply_rounded_corners(self) -> None:
        """Apply a rounded corner effect to the video player."""
        width: int = int(max(self.contentsRect().size().width(), 0))
        height: int = int(max(self.contentsRect().size().height(), 0))
        mask = Image.new(
            "RGBA",
            (
                width,
                height,
            ),
            (0, 0, 0, 255),
        )
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            (0, 0) + (width, height),
            radius=8,
            fill=(0, 0, 0, 0),
        )
        final_mask = mask.getchannel("A").toqpixmap()
        self.setMask(QRegion(QBitmap(final_mask)))

    def set_tint_opacity(self, opacity: int) -> None:
        """Set the opacity of the video player's tint.

        Args:
            opacity(int): The opacity value, from 0-255.
        """
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.8, QColor(0, 0, 0, 0))
        gradient.setColorAt(1, QColor(0, 0, 0, opacity))
        self.tint.setBrush(QBrush(gradient))

    @override
    def underMouse(self) -> bool:  # noqa: N802
        self.animation.setStartValue(0)
        self.animation.setEndValue(160)
        self.animation.setDuration(125)
        self.animation.start()
        self.timeline_slider.show()
        self.play_pause.show()
        self.mute_unmute.show()
        self.position_label.show()

        return super().underMouse()

    @override
    def releaseMouse(self) -> None:  # noqa: N802
        self.animation.setStartValue(160)
        self.animation.setEndValue(0)
        self.animation.setDuration(125)
        self.animation.start()
        self.timeline_slider.hide()
        self.play_pause.hide()
        self.mute_unmute.hide()
        self.volume_slider.hide()
        self.position_label.hide()

        return super().releaseMouse()

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Pause media if background is clicked, with buffer around controls
        buffer: int = 6
        if event.y() < (self.height() - self.controls.height() - buffer):
            self.toggle_play()
        return super().mousePressEvent(event)

    @override
    def eventFilter(self, arg__1: QObject, arg__2: QEvent) -> bool:
        """Manage events for the media player."""
        if (
            arg__2.type() == QEvent.Type.MouseButtonPress
            and arg__2.button() == Qt.MouseButton.LeftButton  # type: ignore
        ):
            if arg__1 == self.play_pause:
                self.toggle_play()
            elif arg__1 == self.mute_unmute:
                self.toggle_mute()
        elif arg__2.type() is QEvent.Type.Enter:
            if arg__1 == self or arg__1 == self.video_preview:
                self.underMouse()
            elif arg__1 == self.mute_unmute:
                self.volume_slider.show()
        elif arg__2.type() == QEvent.Type.Leave:
            if arg__1 == self or arg__1 == self.video_preview:
                self.releaseMouse()
            elif arg__1 == self.sub_controls:
                self.volume_slider.hide()

        return super().eventFilter(arg__1, arg__2)

    def format_time(self, ms: int) -> str:
        """Format the given time.

        Formats the given time in ms to a nicer format.

        Args:
            ms: Time in ms

        Returns:
            A formatted time: "1:43"

            The formatted time will only include the hour if
            the provided time is at least 60 minutes.
        """
        time = gmtime(ms / 1000)
        return (
            f"{time.tm_hour}:{time.tm_min}:{time.tm_sec:02}"
            if time.tm_hour > 0
            else f"{time.tm_min}:{time.tm_sec:02}"
        )

    def toggle_play(self) -> None:
        """Toggle the playing state of the media."""
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
        self.load_toggle_play_icon(playing)

    def muted_changed(self, muted: bool) -> None:
        self.load_mute_unmute_icon(muted)

    def has_video_changed(self, video_available: bool) -> None:
        if not self.video_preview:
            return
        if video_available:
            self.scene().addItem(self.video_preview)
            self.video_preview.setZValue(-1)
            self.player.setVideoOutput(self.video_preview)
        else:
            self.scene().removeItem(self.video_preview)

    def stop(self) -> None:
        """Clear the filepath, stop the player and release the source."""
        self.filepath = None
        self.player.setSource(QUrl())

    def play(self, filepath: Path) -> None:
        """Set the source of the QMediaPlayer and play."""
        self.filepath = filepath
        if not self.is_paused:
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(self.filepath))

            if self.autoplay.isChecked():
                self.player.play()
        else:
            self.player.setSource(QUrl.fromLocalFile(self.filepath))

    def load_toggle_play_icon(self, playing: bool) -> None:
        icon = self.driver.rm.pause_icon if playing else self.driver.rm.play_icon
        self.play_pause.load(icon)

    def load_mute_unmute_icon(self, muted: bool) -> None:
        icon = self.driver.rm.volume_mute_icon if muted else self.driver.rm.volume_icon
        self.mute_unmute.load(icon)

    def slider_value_changed(self, value: int) -> None:
        if self.timeline_slider.isSliderDown():
            self.player.setPosition(value)
            self.player.setPlaybackRate(0.0001)

        current = self.format_time(value)
        duration = self.format_time(self.player.duration())
        self.position_label.setText(f"{current} / {duration}")

    def slider_released(self) -> None:
        was_playing = self.player.isPlaying()
        self.player.setPosition(self.timeline_slider.value())
        self.player.setPlaybackRate(1)  # Restore from slider_value_changed()

        # Setting position causes the player to start playing again
        if not was_playing:
            self.player.pause()

    def player_position_changed(self, position: int) -> None:
        if not self.timeline_slider.isSliderDown():
            # User isn't using the slider, so update position in widgets
            self.timeline_slider.setValue(position)
            current = self.format_time(self.player.position())
            duration = self.format_time(self.player.duration())
            self.position_label.setText(f"{current} / {duration}")

    def media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        # We can only set the slider duration once we know the size of the media
        if status == QMediaPlayer.MediaStatus.LoadedMedia and self.filepath is not None:
            self.timeline_slider.setMinimum(0)
            self.timeline_slider.setMaximum(self.player.duration())

            current = self.format_time(self.player.position())
            duration = self.format_time(self.player.duration())
            self.position_label.setText(f"{current} / {duration}")

    def _update_controls(self, size: QSize) -> None:
        self.scene().setSceneRect(0, 0, size.width(), size.height())

        # Occupy entire scene width
        self.controls.setMinimumWidth(size.width())
        self.controls.setMaximumWidth(size.width())

        self.controls.move(0, int(self.scene().height() - self.controls.height()))

        ps_w = self.controls.width() - 5
        self.timeline_slider.setMinimumWidth(ps_w)
        self.timeline_slider.setMaximumWidth(ps_w)

        if self.video_preview:
            self.video_preview.setSize(self.size())
            if self.player.hasVideo():
                self.centerOn(self.video_preview)

        self.tint.setRect(0, 0, self.size().width(), self.size().height())
        self.apply_rounded_corners()

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self._update_controls(event.size())

    def volume_slider_changed(self, position: int) -> None:
        self.player.audioOutput().setVolume(position / 100)


class VideoPreview(QGraphicsVideoItem):
    @override
    def boundingRect(self):
        return QRectF(0, 0, self.size().width(), self.size().height())
