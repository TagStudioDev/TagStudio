# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import time
from typing import override

from PySide6.QtCore import QEasingCurve, QRectF, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import (
    QColor,
    QHideEvent,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QResizeEvent,
    QShowEvent,
)
from PySide6.QtWidgets import QWidget


class RoundedProgressBar(QWidget):
    """A custom stylized progress bar that supports smooth animations and rounded corners."""

    MARQUEE_FRACTION = 0.5
    MARQUEE_INTERVAL_MS = 8
    MARQUEE_CYCLE_MS = 2000
    VALUE_ANIMATION_MS = 150
    FADE_MS = 2000

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 0
        self._value = 0

        self._displayed_value = 0.0
        self._corner_radius = 0.0
        self._chunk_color = QColor(Qt.GlobalColor.transparent)
        self._marquee_start: float | None = None
        self._cached_path: QPainterPath | None = None

        self._opacity = 1.0
        self._pending_range_change = False

        self._marquee_timer = QTimer(self)
        self._marquee_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._marquee_timer.setInterval(self.MARQUEE_INTERVAL_MS)
        self._marquee_timer.timeout.connect(self.update)

        self._value_anim = QVariantAnimation(self)
        self._value_anim.setDuration(self.VALUE_ANIMATION_MS)
        self._value_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._value_anim.valueChanged.connect(self._on_value_anim_changed)
        self._value_anim.finished.connect(self._on_value_anim_finished)

        self._fade_anim = QVariantAnimation(self)
        self._fade_anim.setDuration(self.FADE_MS)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.valueChanged.connect(self._on_fade_anim_changed)

    def _on_value_anim_changed(self, value: float) -> None:
        self._displayed_value = value
        self.update()

    def _on_value_anim_finished(self) -> None:
        """Start the fade-out once the progress bar has reached its maximum."""
        if not self._is_indeterminate() and self._value >= self._maximum:
            self._fade_anim.stop()
            self._fade_anim.setStartValue(self._opacity)
            self._fade_anim.setEndValue(0.0)
            self._fade_anim.start()

    def _on_fade_anim_changed(self, value: float) -> None:
        """Update the fill opacity for the fade animation."""
        self._opacity = value
        self.update()

    def _reset_fade(self) -> None:
        """Stop any fading and reset opacity back to full."""
        self._fade_anim.stop()
        if self._opacity != 1.0:
            self._opacity = 1.0
            self.update()

    def set_range(self, minimum: int, maximum: int) -> None:
        """Set the value range, switching to indeterminate mode if maximum <= minimum."""
        if (minimum, maximum) == (self._minimum, self._maximum):
            return

        self._pending_range_change = True
        self._minimum = minimum
        self._maximum = maximum
        if self._is_indeterminate():
            self._reset_fade()
        self._sync_marquee_timer()
        self.update()

    def set_value(self, value: int) -> None:
        """Animate the fill towards `value`."""
        self._value = value
        if self._is_indeterminate():
            self._pending_range_change = False
            return
        if self._pending_range_change:
            self._pending_range_change = False
            if value >= self._maximum:
                self._value_anim.stop()
                self._displayed_value = float(self._maximum)
                self.update()
                self._on_value_anim_finished()
                return

            self._displayed_value = float(self._minimum)
            self._reset_fade()
        elif value < self._maximum:
            self._reset_fade()
        self._value_anim.stop()
        self._value_anim.setStartValue(self._displayed_value)
        self._value_anim.setEndValue(float(value))
        self._value_anim.start()

    def set_corner_radius(self, radius: float) -> None:
        """Set the bottom corner radius and invalidate the cached QPainterPath."""
        self._corner_radius = radius
        self._cached_path = None
        self.update()

    def set_chunk_color(self, color: QColor) -> None:
        """Set the fill color."""
        self._chunk_color = color
        self.update()

    def _is_indeterminate(self) -> bool:
        """Whether the bar is in indeterminate (marquee) mode."""
        return self._maximum <= self._minimum

    def _sync_marquee_timer(self) -> None:
        """Start or stop the marquee timer to match the current mode/visibility."""
        if self._is_indeterminate() and self.isVisible():
            if self._marquee_start is None:
                self._marquee_start = time.monotonic()
            if not self._marquee_timer.isActive():
                self._marquee_timer.start()
        else:
            self._marquee_timer.stop()
            self._marquee_start = None

    def _marquee_fraction(self) -> float:
        """Return the marquee's current position as a fraction of its cycle."""
        if self._marquee_start is None:
            return 0.0
        elapsed_ms = (time.monotonic() - self._marquee_start) * 1000
        return (elapsed_ms % self.MARQUEE_CYCLE_MS) / self.MARQUEE_CYCLE_MS

    @override
    def showEvent(self, event: QShowEvent) -> None:
        """Resume the marquee timer when the bar becomes visible."""
        super().showEvent(event)
        self._sync_marquee_timer()

    @override
    def hideEvent(self, event: QHideEvent) -> None:
        """Stop all animations and reset state when the bar is hidden."""
        super().hideEvent(event)
        self._marquee_timer.stop()
        self._marquee_start = None
        self._value_anim.stop()
        self._reset_fade()
        self._pending_range_change = False

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._cached_path = None  # Invalidate the cached QPainterPath on resize

    def _bottom_rounded_path(self, rect: QRectF) -> QPainterPath:
        """Return the bottom-rounded clip path for `rect`."""
        if self._cached_path is not None:
            return self._cached_path

        # TODO: Currently these values are hardcoded for use with the Banner widget, but this
        # could be made customizable to specify the exact rounding configuration.
        # If you're reading this and want to make use of this progress bar, there you go.
        radius = max(0.0, min(self._corner_radius, rect.width() / 2))
        diam = radius * 2
        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right(), rect.top())
        path.lineTo(rect.right(), rect.bottom() - radius)
        path.arcTo(QRectF(rect.right() - diam, rect.bottom() - diam, diam, diam), 0, -90)
        path.lineTo(rect.left() + radius, rect.bottom())
        path.arcTo(QRectF(rect.left(), rect.bottom() - diam, diam, diam), -90, -90)
        path.closeSubpath()
        self._cached_path = path
        return path

    def _marquee_gradient(self, full_chunk_rect: QRectF) -> QLinearGradient:
        """Gradient for the indeterminate marquee mode (Transparent -> Color -> Transparent)."""
        gradient = QLinearGradient(full_chunk_rect.left(), 0, full_chunk_rect.right(), 0)
        transparent = QColor(self._chunk_color)
        transparent.setAlpha(0)
        gradient.setColorAt(0.0, transparent)
        gradient.setColorAt(0.5, self._chunk_color)
        gradient.setColorAt(1.0, transparent)
        return gradient

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        # Paint the marquee or normal chunk fill, clipped to the rounded bottom corners.
        rect = QRectF(self.rect())

        if self._is_indeterminate():
            chunk_width = rect.width() * self.MARQUEE_FRACTION
            travel = rect.width() * (1 + self.MARQUEE_FRACTION)
            chunk_left = (self._marquee_fraction() * travel) - chunk_width
            full_chunk_rect = QRectF(chunk_left, 0, chunk_width, rect.height())
            chunk_rect = full_chunk_rect.intersected(rect)
            if chunk_rect.isEmpty():
                return
            fill = self._marquee_gradient(full_chunk_rect)
        else:
            fraction = (self._displayed_value - self._minimum) / (self._maximum - self._minimum)
            fraction = max(0.0, min(1.0, fraction))
            chunk_rect = QRectF(0, 0, rect.width() * fraction, rect.height()).intersected(rect)
            if chunk_rect.isEmpty():
                return
            fill = self._chunk_color

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipPath(self._bottom_rounded_path(rect))
        painter.setOpacity(self._opacity)
        painter.fillRect(chunk_rect, fill)
        painter.end()
