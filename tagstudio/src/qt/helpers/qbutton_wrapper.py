# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PySide6.QtWidgets import QPushButton


class QPushButtonWrapper(QPushButton):
    """Custom QPushButton wrapper.

    This is a customized implementation of the PySide6 QPushButton that allows to suppress
    the warning that is triggered by disconnecting a signal that is not currently connected.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_connected = False
