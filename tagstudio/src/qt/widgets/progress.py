# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressDialog


class ProgressWidget(QWidget):
    """Prebuilt thread-safe progress bar widget."""

    def __init__(
        self,
        window_title: str,
        label_text: str,
        cancel_button_text: Optional[str],
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
        self.setWindowFlags(
            self.pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowTitle(window_title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def update_label(self, text: str):
        self.pb.setLabelText(text)

    def update_progress(self, value: int):
        self.pb.setValue(value)
