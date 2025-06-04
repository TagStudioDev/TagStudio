# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Callable

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QProgressDialog, QVBoxLayout, QWidget

from tagstudio.qt.helpers.custom_runnable import CustomRunnable
from tagstudio.qt.helpers.function_iterator import FunctionIterator


class ProgressWidget(QWidget):
    """Prebuilt thread-safe progress bar widget."""

    def __init__(
        self,
        *,
        window_title: str = "",
        label_text: str = "",
        cancel_button_text: str | None,
        minimum: int,
        maximum: int,
    ):
        super().__init__()
        self.root = QVBoxLayout(self)
        self.pb = QProgressDialog(
            labelText=label_text,
            minimum=minimum,
            cancelButtonText=cancel_button_text,
            maximum=maximum,
        )
        self.root.addWidget(self.pb)
        self.setFixedSize(432, 112)
        self.setWindowFlags(self.pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle(window_title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def update_label(self, text: str):
        self.pb.setLabelText(text)

    def update_progress(self, value: int):
        self.pb.setValue(value)

    def _update_progress_unknown_iterable(self, value):
        if hasattr(value, "__getitem__"):
            self.update_progress(value[0] + 1)
        else:
            self.update_progress(value + 1)

    def from_iterable_function(
        self, function: Callable, update_label_callback: Callable | None, *done_callbacks
    ):
        """Display the progress widget from a threaded iterable function."""
        iterator = FunctionIterator(function)
        iterator.value.connect(lambda x: self._update_progress_unknown_iterable(x))
        if update_label_callback:
            iterator.value.connect(lambda x: self.update_label(update_label_callback(x)))

        self.show()

        r = CustomRunnable(lambda: iterator.run())
        r.done.connect(
            lambda: (self.hide(), self.deleteLater(), [callback() for callback in done_callbacks])  # type: ignore
        )
        QThreadPool.globalInstance().start(r)
