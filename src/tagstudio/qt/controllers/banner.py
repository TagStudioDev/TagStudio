# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import time
from collections.abc import Callable, Hashable
from enum import Enum
from typing import Literal, override

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
    SignalInstance,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPaintEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from tagstudio.qt.views.banner_view import BannerView
from tagstudio.qt.views.styles.stylesheets import (
    BANNER_CORNER_RADIUS,
    banner_notice_bg_color,
    banner_notice_style,
    banner_progress_bg_color,
    banner_progress_chunk_color,
    banner_progress_style,
)

BannerMode = Literal["progress", "notice", "fleeting_notice"]


class _BannerBackground(QWidget):
    """The banner's background widget. Used for custom animations, like fading the color."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bg_color = QColor(Qt.GlobalColor.transparent)

    @property
    def bg_color(self) -> QColor:
        return self._bg_color

    def set_bg_color(self, color: QColor) -> None:
        self._bg_color = color
        self.update()

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), BANNER_CORNER_RADIUS, BANNER_CORNER_RADIUS)
        painter.fillPath(path, self._bg_color)
        painter.end()


class Banner(QWidget):
    """The base class for a notification banner.

    Can include text, a determinate or indeterminate progress bar, action button, and close button.
    """

    CONTENT_HEIGHT = 36
    GAP = 6
    HEIGHT = CONTENT_HEIGHT + GAP
    ANIMATION_MS = 250
    COLOR_ANIMATION_MS = 250
    MIN_VISIBLE_MS = 3000

    progress_cancelled = Signal()
    closed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(0)
        self.setMaximumHeight(0)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, self.GAP)
        outer_layout.setSpacing(0)

        self._background = _BannerBackground(self)
        self._background.setObjectName("banner")
        self.view = BannerView()
        self._background.setLayout(self.view)
        outer_layout.addWidget(self._background)

        # The stack key is used to identify this particular banner in a BannerStack.
        # Subclasses should use a static key (like "sync") if new stages are meant to replace
        # the same banner instead of spawning new ones entirely.
        # If a subclass is intended to spawn multiple parallel banners, use uniquely generated keys.
        self.stack_key: Hashable | None = None
        self._stage: Enum | None = None
        self._action_signal: SignalInstance | None = None
        self._mode: BannerMode = "progress"
        self._notice_style = banner_notice_style()
        self._progress_style = banner_progress_style()
        self._notice_bg_color = banner_notice_bg_color()
        self._progress_bg_color = banner_progress_bg_color()
        self._background.setStyleSheet(self._notice_style)
        self._background.set_bg_color(self._notice_bg_color)
        self.view.progress_bar.set_corner_radius(BANNER_CORNER_RADIUS)
        self.view.progress_bar.set_chunk_color(banner_progress_chunk_color())

        self._card_color_anim = QVariantAnimation(self)
        self._card_color_anim.setDuration(self.COLOR_ANIMATION_MS)
        self._card_color_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._card_color_anim.valueChanged.connect(self._background.set_bg_color)

        self._connect_callbacks()
        self._set_mode("notice")

        self._height_anim = QPropertyAnimation(self, b"maximumHeight", self)
        self._height_anim.setDuration(self.ANIMATION_MS)
        self._height_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._height_anim.valueChanged.connect(self.setMinimumHeight)
        self._height_anim.finished.connect(self._on_height_anim_finished)

        self._shown_at: float | None = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(lambda: self._start_height_animation(0))

    @property
    def stage(self) -> Enum | None:
        """The banner stage currently being shown, or None while hidden."""
        return self._stage

    def call_when_open(self, callback: Callable[[], None]) -> None:
        """Call `callback` if/when the banner is fully open."""
        if self._is_fully_open():
            callback()
            return

        def _on_finished() -> None:
            self._height_anim.finished.disconnect(_on_finished)
            if self._is_fully_open():
                callback()

        self._height_anim.finished.connect(_on_finished)

    def hide_banner(self, force: bool = False):
        """Hide the banner (if shown).

        Args:
            force (bool): Bypass the minimum visible duration and hide immediately.
        """
        self._animate_to(0, force=force)

    def _show_progress(self, stage: Enum, text: str, value: int = 0, maximum: int = 0) -> None:
        """A progress bar with text. A `maximum` of 0 is shown as indeterminate."""
        self._action_signal = None
        self._set_mode("progress")
        self._enter_stage(stage)
        self.view.label.setText(text)
        self.view.progress_bar.set_range(0, maximum)
        self.view.progress_bar.set_value(value)
        self._animate_to(self.HEIGHT)

    def _show_notice(
        self, stage: Enum, text: str, action_text: str, action: SignalInstance
    ) -> None:
        """A dismissible notice whose button emits `action`."""
        self._action_signal = action
        self._set_mode("notice")
        self._enter_stage(stage)
        self.view.action_button.setText(action_text)
        self.view.label.setText(text)
        self._animate_to(self.HEIGHT)

    def _show_fleeting_notice(self, stage: Enum, text: str) -> None:
        """A non-interactable text notice that hides itself automatically after a few seconds."""
        self._action_signal = None
        self._set_mode("fleeting_notice")
        self._enter_stage(stage)
        self.view.label.setText(text)
        self._animate_to(self.HEIGHT)
        self._animate_to(0)

    def _enter_stage(self, stage: Enum) -> None:
        if stage is self._stage:
            return
        self._stage = stage
        self.view.label.reset_width()

    def _is_fully_open(self) -> bool:
        return (
            self.maximumHeight() == self.HEIGHT
            and self._height_anim.state() != QPropertyAnimation.State.Running
        )

    def _connect_callbacks(self) -> None:
        self.view.close_button.clicked.connect(self._on_dismiss)
        self.view.action_button.clicked.connect(self._on_action_clicked)

    def _on_action_clicked(self) -> None:
        if self._action_signal is not None:
            self._action_signal.emit()

    def _on_height_anim_finished(self) -> None:
        if self.maximumHeight() == 0:
            self._stage = None
            self._shown_at = None
            self.closed.emit()
        else:
            self._shown_at = time.monotonic()

    def _start_height_animation(self, target_height: int) -> None:
        if self.maximumHeight() == target_height and self._height_anim.state() != (
            QPropertyAnimation.State.Running
        ):
            return
        self._height_anim.stop()
        self._height_anim.setStartValue(self.maximumHeight())
        self._height_anim.setEndValue(target_height)
        self._height_anim.start()

    def _animate_to(self, target_height: int, force: bool = False) -> None:
        self._hide_timer.stop()
        if target_height > 0:
            if self._is_fully_open():
                self._shown_at = time.monotonic()
            self._start_height_animation(target_height)
            return

        if force:
            self._start_height_animation(0)
            return

        if self._shown_at is None:  # Still opening
            self.call_when_open(lambda: self._animate_to(0))
            return

        remaining_ms = self.MIN_VISIBLE_MS - (time.monotonic() - self._shown_at) * 1000
        if remaining_ms > 0:
            self._hide_timer.start(int(remaining_ms))
            return
        self._start_height_animation(0)

    def _set_mode(self, mode: BannerMode):
        if mode == self._mode:
            return

        self._mode = mode
        self.view.label.reset_width()
        self.view.close_button.setVisible(mode != "fleeting_notice")
        self.view.action_button.setVisible(mode == "notice")
        self.view.progress_bar.setVisible(mode == "progress")

        # The progress bar state gets a darkened background, while notices get the accent color.
        is_progress = mode == "progress"
        self._background.setStyleSheet(self._progress_style if is_progress else self._notice_style)

        target_color = self._progress_bg_color if is_progress else self._notice_bg_color
        self._card_color_anim.stop()
        self._card_color_anim.setStartValue(self._background.bg_color)
        self._card_color_anim.setEndValue(target_color)
        self._card_color_anim.start()

    def _on_dismiss(self):
        if self._mode == "progress":
            self.progress_cancelled.emit()
        # Explicit dismiss, apply immediately
        self._animate_to(0, force=True)
