# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing
from pathlib import Path
from time import gmtime

from PIL import Image, ImageDraw
from PySide6.QtCore import QEvent, QObject, QRectF, Qt, QUrl, QVariantAnimation
from PySide6.QtGui import QAction, QBitmap, QBrush, QColor, QFont, QPen, QRegion, QResizeEvent
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QSlider,
)

from tagstudio.core.enums import SettingItems
from tagstudio.qt.helpers.file_opener import FileOpenerHelper
from tagstudio.qt.helpers.qslider_wrapper import QClickSlider
from tagstudio.qt.platform_strings import open_file_str
from tagstudio.qt.translations import Translations

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class MediaPlayer(QGraphicsView):
    """A basic media player widget.

    Gives a basic control set to manage media playback.
    """

    # These mouse_over_* variables are used to help
    # determine if a mouse click should be handled
    # by the media player or by some parent widget.
    mouse_over_volume_slider = False
    mouse_over_play_pause = False
    mouse_over_mute_unmute = False

    video_preview = None

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
        self.pslider = QClickSlider()
        self.pslider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.pslider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.pslider.setSingleStep(1)
        self.pslider.setOrientation(Qt.Orientation.Horizontal)
        self.pslider.setStyleSheet(slider_style)
        self.pslider.sliderReleased.connect(self.slider_released)
        self.pslider.valueChanged.connect(self.slider_value_changed)
        self.pslider.hide()

        self.play_pause = QSvgWidget()
        self.play_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_pause.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, on=True)
        self.play_pause.setMouseTracking(True)
        self.play_pause.installEventFilter(self)
        self.load_toggle_play_icon(playing=False)
        self.play_pause.resize(24, 24)
        self.play_pause.hide()

        self.mute_unmute = QSvgWidget()
        self.mute_unmute.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_unmute.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, on=True)
        self.mute_unmute.setMouseTracking(True)
        self.mute_unmute.installEventFilter(self)
        self.load_mute_unmute_icon(muted=False)
        self.mute_unmute.resize(24, 24)
        self.mute_unmute.hide()

        self.volume_slider = QClickSlider()
        self.volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.volume_slider.setValue(int(self.player.audioOutput().volume() * 100))
        self.volume_slider.valueChanged.connect(self.volume_slider_changed)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setStyleSheet(slider_style)
        self.volume_slider.hide()

        self.position_label = self.scene().addText("0:00")
        self.position_label.hide()

        font = QFont()
        font.setPointSize(11)
        self.position_label.setFont(font)
        self.position_label.setDefaultTextColor(QColor(255, 255, 255, 255))
        self.position_label.hide()

        self.scene().addWidget(self.pslider)
        self.scene().addWidget(self.play_pause)
        self.scene().addWidget(self.mute_unmute)
        self.scene().addWidget(self.volume_slider)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.opener = FileOpenerHelper(filepath=self.filepath)
        autoplay_action = QAction(Translations["media_player.autoplay"], self)
        autoplay_action.setCheckable(True)
        self.addAction(autoplay_action)
        autoplay_action.setChecked(
            self.driver.settings.value(SettingItems.AUTOPLAY, defaultValue=True, type=bool)
        )
        autoplay_action.triggered.connect(lambda: self.toggle_autoplay())
        self.autoplay = autoplay_action

        open_file_action = QAction(Translations["media_player.autoplay"], self)
        open_file_action.triggered.connect(self.opener.open_file)

        open_explorer_action = QAction(open_file_str(), self)

        open_explorer_action.triggered.connect(self.opener.open_explorer)
        self.addAction(open_file_action)
        self.addAction(open_explorer_action)

    def set_video_output(self, video: QGraphicsVideoItem):
        self.player.setVideoOutput(video)

    def toggle_autoplay(self) -> None:
        """Toggle the autoplay state of the video."""
        self.driver.settings.setValue(SettingItems.AUTOPLAY, self.autoplay.isChecked())
        self.driver.settings.sync()

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
        self.volume_slider.show()
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

    def mouse_over_elements(self) -> bool:
        return (
            self.mouse_over_play_pause
            or self.mouse_over_mute_unmute
            or self.mouse_over_volume_slider
        )

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        """Manage events for the media player."""
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton  # type: ignore
        ):
            if obj == self.play_pause:
                self.toggle_play()
            elif obj == self.mute_unmute:
                self.toggle_mute()
            elif self.mouse_over_elements() is False:
                self.toggle_play()
        elif event.type() is QEvent.Type.Enter:
            if obj == self or obj == self.video_preview:
                self.underMouse()
            elif obj == self.mute_unmute:
                self.mouse_over_mute_unmute = True
            elif obj == self.play_pause:
                self.mouse_over_play_pause = True
            elif obj == self.volume_slider:
                self.mouse_over_volume_slider = True
        elif event.type() == QEvent.Type.Leave:
            if obj == self or obj == self.video_preview:
                self.releaseMouse()
            elif obj == self.mute_unmute:
                self.mouse_over_mute_unmute = False
            elif obj == self.play_pause:
                self.mouse_over_play_pause = False
            elif obj == self.volume_slider:
                self.mouse_over_volume_slider = False

        return super().eventFilter(obj, event)

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
        if video_available:
            self.scene().addItem(self.video_preview)
            self.video_preview.setZValue(-1)
            self.player.setVideoOutput(self.video_preview)
        else:
            self.scene().removeItem(self.video_preview)

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

            if self.autoplay.isChecked():
                self.player.play()
        else:
            self.player.setSource(QUrl.fromLocalFile(self.filepath))

        self.opener.set_filepath(self.filepath)

    def load_toggle_play_icon(self, playing: bool) -> None:
        icon = self.driver.rm.pause_icon if playing else self.driver.rm.play_icon
        self.play_pause.load(icon)
        # self.set_icon(self.toggle_play, icon)

    def load_mute_unmute_icon(self, muted: bool) -> None:
        icon = self.driver.rm.volume_mute_icon if muted else self.driver.rm.volume_icon
        self.mute_unmute.load(icon)

    def slider_value_changed(self, value: int) -> None:
        current = self.format_time(value)
        duration = self.format_time(self.player.duration())
        self.position_label.setPlainText(f"{current} / {duration}")
        self._move_position_label()

    def slider_released(self) -> None:
        was_playing = self.player.isPlaying()
        self.player.setPosition(self.pslider.value())

        # Setting position causes the player to start playing again.
        # We should reset back to initial state.
        if not was_playing:
            self.player.pause()

    def player_position_changed(self, position: int) -> None:
        if self.pslider.mouse_pressed:
            self.player.setPosition(self.pslider.value())
            self.pslider.mouse_pressed = False
        elif not self.pslider.isSliderDown():
            # User isn't using the slider, so update position in widgets.
            self.pslider.setValue(position)
            current = self.format_time(self.player.position())
            duration = self.format_time(self.player.duration())
            self.position_label.setPlainText(f"{current} / {duration}")
            self._move_position_label()

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
            self.position_label.setPlainText(f"{current} / {duration}")
            self._move_position_label()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        size = event.size()

        self.scene().setSceneRect(0, 0, size.width(), size.height())

        self.play_pause.move(0, int(self.scene().height() - self.play_pause.height()))
        self.mute_unmute.move(
            self.play_pause.width(), int(self.scene().height() - self.mute_unmute.height())
        )

        self._move_position_label()

        self.pslider.setMinimumWidth(self.size().width() - 10)
        self.pslider.setMaximumWidth(self.size().width() - 10)
        self.pslider.move(
            3, int(self.scene().height() - self.play_pause.height() - self.pslider.height())
        )

        pos_w = int(self.play_pause.width() + self.mute_unmute.width())
        pos_h = int(size.height() - self.mute_unmute.height() + 5)
        self.volume_slider.move(pos_w, pos_h)

        self.video_preview.setSize(self.size())
        if self.player.hasVideo():
            self.centerOn(self.video_preview)

        self.tint.setRect(0, 0, self.size().width(), self.size().height())
        self.apply_rounded_corners()

    def _move_position_label(self):
        """Convenience function for repositioning the position label.

        This is needed because the position label is not automatically
        resized after changing the text.
        """
        rect = self.position_label.boundingRect()
        pos_w = int(self.size().width() - rect.width() - 2)
        pos_h = int(self.size().height() - self.mute_unmute.size().height() - 2)
        self.position_label.setPos(pos_w, pos_h)

    def volume_slider_changed(self, position: int) -> None:
        self.player.audioOutput().setVolume(position / 100)


class VideoPreview(QGraphicsVideoItem):
    def boundingRect(self):  # noqa: N802
        return QRectF(0, 0, self.size().width(), self.size().height())

    def paint(self, painter, option, widget=None) -> None:
        # painter.brush().setColor(QColor(0, 0, 0, 255))
        # You can set any shape you want here.
        # RoundedRect is the standard rectangle with rounded corners.
        # With 2nd and 3rd parameter you can tweak the curve until you get what you expect

        super().paint(painter, option, widget)
