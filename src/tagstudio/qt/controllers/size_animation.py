# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import (
    QAbstractAnimation,
    QCoreApplication,
    QEasingCurve,
    QEvent,
    QSignalBlocker,
    QVariantAnimation,
    Signal,
)
from PySide6.QtWidgets import QSplitter, QWidget

DURATION = 250  # Milliseconds


class SizeAnimation(QVariantAnimation):
    """Shows or hides a widget by animating its height.

    In a splitter, its largest shown neighbor gives or takes the height.
    """

    height_set = Signal(float)

    def __init__(self, widget: QWidget) -> None:
        super().__init__(widget)
        self._widget = widget
        self._max_height = widget.maximumHeight()
        self._is_shown = not widget.isHidden()
        self._shown_height: int | None = None
        self._collapsed_height: int | None = None
        self.setDuration(DURATION)
        self.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.valueChanged.connect(self._set_height)
        self.finished.connect(self._finish)

    def set_shown(self, shown: bool, height: int | None = None) -> None:
        """Show or hide the widget, animating its height."""
        is_running = self.state() == QAbstractAnimation.State.Running
        if (self._is_shown if is_running else not self._widget.isHidden()) == shown:
            return
        self._is_shown = shown
        if is_running:
            start = float(self.currentValue())
        else:
            start = 0.0 if self._widget.isHidden() else float(self._widget.height())
        self.stop()
        if not shown and start > 0:
            self._shown_height = round(start)
        if not self._widget.window().isVisible():
            self._finish()
            return
        end = 0.0
        if shown:
            end = float(height or self.full_height())
            self._set_height(start)
            self._widget.setHidden(False)
        self._animate(start, end)

    def collapse_to(self, height: int) -> None:
        """Collapse to this height."""
        if self.state() != QAbstractAnimation.State.Running:
            is_visible = self._widget.window().isVisible()
            self._shown_height = self._widget.height() if is_visible else self.full_height()
        self._animate_to_end(height, height)

    def expand_to(self, height: int) -> None:
        """Expand to this height."""
        self._animate_to_end(None, height)

    def _animate_to_end(self, collapsed_height: int | None, end: int) -> None:
        is_running = self.state() == QAbstractAnimation.State.Running
        start = float(self.currentValue()) if is_running else float(self._widget.height())
        self._collapsed_height = collapsed_height
        self.stop()
        if self._widget.window().isVisible():
            self._animate(start, float(end))
        else:
            self._finish()

    def _animate(self, start: float, end: float) -> None:
        # Block setting these so the widget doesn't jump to the end height before it starts
        with QSignalBlocker(self):
            self.setStartValue(start)
            self.setEndValue(end)
        self.start()

    def full_height(self) -> int:
        """The height to animate to when opening."""
        return self._shown_height or self._widget.sizeHint().height()

    def _set_height(self, height: float) -> None:
        self._widget.setMaximumHeight(round(height))
        splitter = self._widget.parentWidget()
        if isinstance(splitter, QSplitter):
            index = splitter.indexOf(self._widget)
            sizes = splitter.sizes()
            neighbors = [i for i, size in enumerate(sizes) if i != index and size > 0]
            if neighbors:
                largest = max(neighbors, key=lambda i: sizes[i])
                sizes[largest] += sizes[index] - round(height)
                sizes[index] = round(height)
                splitter.setSizes(sizes)
        self.height_set.emit(height)
        # Lay out now so no frame paints between the queued layout passes
        QCoreApplication.sendPostedEvents(None, QEvent.Type.LayoutRequest.value)

    def _finish(self) -> None:
        self._widget.setMaximumHeight(self._collapsed_height or self._max_height)
        self._widget.setHidden(not self._is_shown)
