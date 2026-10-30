# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QVariantAnimation
from PySide6.QtWidgets import QSplitter, QWidget

DURATION = 250  # Milliseconds


class SizeAnimation(QVariantAnimation):
    """Shows or hides a widget by animating its height.

    In a splitter, its largest shown neighbor gives or takes the height.
    """

    def __init__(self, widget: QWidget) -> None:
        super().__init__(widget)
        self._widget = widget
        self._max_height = widget.maximumHeight()
        self._is_shown = not widget.isHidden()
        self._shown_height: int | None = None
        self.setDuration(DURATION)
        self.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.valueChanged.connect(self._set_height)
        self.finished.connect(self._finish)

    def set_shown(self, shown: bool, height: int | None = None, is_animated: bool = True) -> None:
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
        if not is_animated or not self._widget.window().isVisible():
            self._finish()
            return
        end = 0.0
        if shown:
            end = float(height or self._shown_height or self._widget.sizeHint().height())
            self._set_height(start)
            self._widget.setHidden(False)
        self.setStartValue(start)
        self.setEndValue(end)
        self.start()

    def _set_height(self, height: float) -> None:
        self._widget.setMaximumHeight(round(height))
        splitter = self._widget.parentWidget()
        if not isinstance(splitter, QSplitter):
            return
        index = splitter.indexOf(self._widget)
        sizes = splitter.sizes()
        neighbors = [i for i, size in enumerate(sizes) if i != index and size > 0]
        if neighbors:
            largest = max(neighbors, key=lambda i: sizes[i])
            sizes[largest] += sizes[index] - round(height)
            sizes[index] = round(height)
            splitter.setSizes(sizes)

    def _finish(self) -> None:
        self._widget.setMaximumHeight(self._max_height)
        self._widget.setHidden(not self._is_shown)
