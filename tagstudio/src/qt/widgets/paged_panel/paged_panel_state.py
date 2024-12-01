# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtWidgets import QPushButton
from src.qt.widgets.paged_panel.paged_body_wrapper import PagedBodyWrapper


class PagedPanelState:
    """A state object for paged panels."""

    def __init__(
        self,
        title: str,
        body_wrapper: PagedBodyWrapper,
        buttons: list[QPushButton | int],
        connect_to_back=list[QPushButton],
        connect_to_next=list[QPushButton],
    ):
        self.title: str = title
        self.body_wrapper: PagedBodyWrapper = body_wrapper
        self.buttons: list[QPushButton | int] = buttons
        self.connect_to_back: list[QPushButton] = connect_to_back
        self.connect_to_next: list[QPushButton] = connect_to_next
