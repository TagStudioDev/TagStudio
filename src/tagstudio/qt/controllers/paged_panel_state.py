# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtWidgets import QPushButton

from tagstudio.qt.views.paged_body_wrapper import PagedBodyWrapper


class PagedPanelState:
    """A state object for paged panels."""

    def __init__(
        self,
        title: str,
        body_wrapper: PagedBodyWrapper,
        buttons: list[QPushButton | int],
        connect_to_back: list[QPushButton],
        connect_to_next: list[QPushButton],
    ):
        self.title: str = title
        self.body_wrapper: PagedBodyWrapper = body_wrapper
        self.buttons: list[QPushButton | int] = buttons
        self.connect_to_back: list[QPushButton] = connect_to_back
        self.connect_to_next: list[QPushButton] = connect_to_next
