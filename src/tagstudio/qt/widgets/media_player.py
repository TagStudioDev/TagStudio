# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing
from pathlib import Path
from time import gmtime
from typing import override

from PIL import Image, ImageDraw
from PySide6.QtCore import QEvent, QObject, QRectF, QSize, Qt, QUrl, QVariantAnimation
from PySide6.QtGui import QAction, QBitmap, QBrush, QColor, QPen, QRegion, QResizeEvent
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    QWidget,
)

from tagstudio.qt.helpers.qslider_wrapper import QClickSlider
from tagstudio.qt.translations import Translations

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


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
            }

            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 2px;
                margin: 2px 0;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background: #6ea0ff;
                border: 1px solid #5c5c5c;
                width: 12px;
                height: 12px;
                margin: -6px 0; 
                border-radius: 6px;
            }

            QSlider::add-page:horizontal {
                background: #3f4144;
                height: 2px;
                margin: 2px 0;
                border-radius: 2px;
            }

            QSlider::sub-page:horizontal {
                background: #6ea0ff;
                height: 2px;
                margin: 2px 0;
                border-radius: 2px;
            }

            QSlider::groove:vertical {
                border: 1px solid #999999;
                width: 2px;
                margin: 0 2px;
                border-radius: 2px;
            }

            QSlider::handle:vertical {
                background: #6ea0ff;
                border: 1px solid #5c5c5c;
                width: 12px;
                height: 12px;
                margin: 0 -6px;
                border-radius: 6px;
            }

            QSlider::add-page:vertical {
                background: #6ea0ff;
                width: 2px;
                margin: 0 2px;
                border-radius: 2px;
            }

            QSlider::sup-page:vertical {
                background: #3f4144;
                width: 2px;
                margin: 0 2px;
                border-radius: 2px;
            }
        """

        # setup the scene
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
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.video_preview = VideoPreview()
        self.video_preview.setAcceptHoverEvents(True)
        self.video_preview.setAcceptedMouseButtons(Qt.MouseButton.RightButton)
        self.video_preview.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.video_preview.installEventFilter(self)

        # animation
        self.animation = QVariantAnimation(self)
        self.animation.valueChanged.connect(lambda value: self.set_tint_opacity(value))

        # Set up the tint.
        self.tint = self.scene().addRect(
            0,
            0,
            self.size().width(),
            self.size().height(),
            QPen(QColor(0, 0, 0, 0)),
            QBrush(QColor(0, 0, 0, 0)),
        )

        # setup the player
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
        self.player.hasVideoChanged.connect(self.has_video_changed)
        self.player.audioOutput().mutedChanged.connect(self.muted_changed)

        # Media controls
        self.master_controls = QWidget()
        master_layout = QGridLayout(self.master_controls)
        master_layout.setContentsMargins(0, 0, 0, 0)
        self.master_controls.setStyleSheet("background: transparent;")
        self.master_controls.setMinimumHeight(75)

        self.pslider = QClickSlider()
        self.pslider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.pslider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.pslider.setSingleStep(1)
        self.pslider.setOrientation(Qt.Orientation.Horizontal)
        self.pslider.setStyleSheet(slider_style)
        self.pslider.sliderReleased.connect(self.slider_released)
        self.pslider.valueChanged.connect(self.slider_value_changed)
        self.pslider.hide()

        master_layout.addWidget(self.pslider, 0, 0, 0, 2)
        master_layout.setAlignment(self.pslider, Qt.AlignmentFlag.AlignCenter)

        fixed_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.sub_controls = QWidget()
        self.sub_controls.setMouseTracking(True)
        self.sub_controls.installEventFilter(self)
        sub_layout = QHBoxLayout(self.sub_controls)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        self.sub_controls.setStyleSheet("background: transparent;")

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

        retain_policy = QSizePolicy()
        retain_policy.setRetainSizeWhenHidden(True)

        self.volume_slider = QClickSlider()
        self.volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.volume_slider.setValue(int(self.player.audioOutput().volume() * 100))
        self.volume_slider.valueChanged.connect(self.volume_slider_changed)
        self.volume_slider.setStyleSheet(slider_style)
        self.volume_slider.setSizePolicy(retain_policy)
        self.volume_slider.hide()

        sub_layout.addWidget(self.volume_slider)
        sub_layout.setAlignment(self.volume_slider, Qt.AlignmentFlag.AlignLeft)

        # Adding a stretch here ensures the rest of the widgets
        # in the sub_layout will not stretch to fill the remaining
        # space.
        sub_layout.addStretch()

        master_layout.addWidget(self.sub_controls, 1, 0)

        self.position_label = QLabel("0:00")
        self.position_label.setStyleSheet("color: #ffffff;")
        master_layout.addWidget(self.position_label, 1, 1)
        master_layout.setAlignment(self.position_label, Qt.AlignmentFlag.AlignRight)
        self.position_label.hide()

        self.scene().addWidget(self.master_controls)

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

        # start the player muted
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
        self.tint.setBrush(QBrush(QColor(0, 0, 0, opacity)))

    def underMouse(self) -> bool:  # noqa: N802
        self.animation.setStartValue(self.tint.brush().color().alpha())
        self.animation.setEndValue(100)
        self.animation.setDuration(250)
        self.animation.start()
        self.pslider.show()
        self.play_pause.show()
        self.mute_unmute.show()
        self.position_label.show()

        return super().underMouse()

    def releaseMouse(self) -> None:  # noqa: N802
        self.animation.setStartValue(self.tint.brush().color().alpha())
        self.animation.setEndValue(0)
        self.animation.setDuration(500)
        self.animation.start()
        self.pslider.hide()
        self.play_pause.hide()
        self.mute_unmute.hide()
        self.volume_slider.hide()
        self.position_label.hide()

        return super().releaseMouse()

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
            else:
                self.toggle_play()
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

    def media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        # We can only set the slider duration once we know the size of the media
        if status == QMediaPlayer.MediaStatus.LoadedMedia and self.filepath is not None:
            self.pslider.setMinimum(0)
            self.pslider.setMaximum(self.player.duration())

            current = self.format_time(self.player.position())
            duration = self.format_time(self.player.duration())
            self.position_label.setText(f"{current} / {duration}")

    def _update_controls(self, size: QSize) -> None:
        self.scene().setSceneRect(0, 0, size.width(), size.height())

        # occupy entire scene width
        self.master_controls.setMinimumWidth(size.width())
        self.master_controls.setMaximumWidth(size.width())

        self.master_controls.move(0, int(self.scene().height() - self.master_controls.height()))

        ps_w = self.master_controls.width() - 5
        self.pslider.setMinimumWidth(ps_w)
        self.pslider.setMaximumWidth(ps_w)

        # Changing the orientation of the volume slider to
        # make it easier to use in smaller sizes.
        orientation = self.volume_slider.orientation()
        if size.width() <= 175 and orientation is Qt.Orientation.Horizontal:
            self.volume_slider.setOrientation(Qt.Orientation.Vertical)
            self.volume_slider.setMaximumHeight(30)
        elif size.width() > 175 and orientation is Qt.Orientation.Vertical:
            self.volume_slider.setOrientation(Qt.Orientation.Horizontal)

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

    @override
    def paint(self, painter, option, widget=None) -> None:
        # painter.brush().setColor(QColor(0, 0, 0, 255))
        # You can set any shape you want here.
        # RoundedRect is the standard rectangle with rounded corners.
        # With 2nd and 3rd parameter you can tweak the curve until you get what you expect

        super().paint(painter, option, widget)
