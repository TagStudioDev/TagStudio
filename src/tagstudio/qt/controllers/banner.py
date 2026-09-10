# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import time
from collections.abc import Callable
from typing import Literal, override

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
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
    """A notification banner with an optional progress bar, action button, and close button."""

    CONTENT_HEIGHT = 36
    GAP = 6
    HEIGHT = CONTENT_HEIGHT + GAP
    ANIMATION_MS = 250
    COLOR_ANIMATION_MS = 250
    MIN_VISIBLE_MS = 3000
    STARTUP_EXTRA_HOLD_MS = 500  # Starting up may eat into time shown, so add extra time.

    notice_action_clicked = Signal()
    cancel_requested = Signal()
    dismissed = Signal()

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

        self._mode: BannerMode = "progress"
        self._progress_phase: object = None
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

        self._shown_at: float | None = None
        self._extra_hold_ms = 0
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(lambda: self._start_height_animation(0))

    def request_extra_duration(self) -> None:
        """Add STARTUP_EXTRA_HOLD_MS to the next automatic hide's minimum-visible window."""
        self._extra_hold_ms = self.STARTUP_EXTRA_HOLD_MS

    def call_when_open(self, callback: Callable[[], None]) -> None:
        """Call `callback` if/when the banner is fully open."""
        if self.maximumHeight() == self.HEIGHT and self._height_anim.state() != (
            QPropertyAnimation.State.Running
        ):
            callback()
            return

        def _on_finished() -> None:
            self._height_anim.finished.disconnect(_on_finished)
            callback()

        self._height_anim.finished.connect(_on_finished)

    def _connect_callbacks(self) -> None:
        self.view.close_button.clicked.connect(self._on_dismiss)
        self.view.action_button.clicked.connect(self._on_action_clicked)

    def _on_action_clicked(self) -> None:
        self.notice_action_clicked.emit()

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
            self._shown_at = time.monotonic()
            self._start_height_animation(target_height)
            return

        extra_hold_ms = self._extra_hold_ms
        self._extra_hold_ms = 0
        if not force and self._shown_at is not None:
            elapsed_ms = (time.monotonic() - self._shown_at) * 1000
            remaining_ms = (self.MIN_VISIBLE_MS + extra_hold_ms) - elapsed_ms
            if remaining_ms > 0:
                self._hide_timer.start(int(remaining_ms))
                return
        self._shown_at = None
        self._start_height_animation(0)

    def _set_mode(self, mode: BannerMode):
        if mode == self._mode:
            return

        self._mode = mode
        self._progress_phase = None
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

    def _present(self, mode: BannerMode, button_text: str, message: str) -> None:
        """Applies the banner mode and any label + button text, then animates the banner open."""
        self._set_mode(mode)
        self.view.action_button.setText(button_text)
        self.view.label.setText(message)
        self._animate_to(self.HEIGHT)

    def _on_dismiss(self):
        if self._mode == "progress":
            self.cancel_requested.emit()
        # Explicit dismiss, apply immediately
        self._animate_to(0, force=True)
        self.dismissed.emit()

    def show_notice(self, message: str, action_text: str) -> None:
        """Show a dismissible notice with an action button, until dismissed or replaced."""
        self._present("notice", action_text, message)

    def show_fleeting_notice(self, message: str) -> None:
        """Show a brief notice with no action button that dismisses itself automatically."""
        self._set_mode("fleeting_notice")
        self.view.label.setText(message)
        self._animate_to(self.HEIGHT)
        # Deferred by the existing MIN_VISIBLE_MS guard, same as an unforced hide_banner().
        self._animate_to(0)

    def show_progress(self, text: str, value: int = 0, maximum: int = 0, phase: str | None = None):
        """Show the progress banner.

        Args:
            text (str): The status text shown in the banner body.
            value (int): The current progress value.
            maximum (int): The maximum progress value. If 0, shown as indeterminate.
            phase (str | None): An identifier for the current sub-phase of progress.
                Helps inform widgets that need to update between phases, like the StableLabel.
        """
        self._set_mode("progress")
        if phase != self._progress_phase:
            self._progress_phase = phase
            self.view.label.reset_width()
        self.view.label.setText(text)
        self.view.progress_bar.set_range(0, maximum)
        self.view.progress_bar.set_value(value)
        self._animate_to(self.HEIGHT)

    def hide_banner(self, force: bool = False):
        """Hide the banner (if shown).

        Args:
            force (bool): Bypass the minimum visible duration and hide immediately.
        """
        self._animate_to(0, force=force)
