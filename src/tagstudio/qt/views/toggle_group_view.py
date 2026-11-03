# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import NamedTuple

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton

from tagstudio.qt.views.styles.color_overlay import toggle_icon
from tagstudio.qt.views.styles.stylesheets import MED_HEIGHT, RADIUS
from tagstudio.qt.views.styles.tagstudio_style import set_checked_by_icon, set_joined_edges

_ICON_SIZE = QSize(18, 18)


class Toggle(NamedTuple):
    svg: bytes
    checked_svg: bytes
    tooltip: str


class ToggleGroupView(QHBoxLayout):
    def __init__(self, toggles: list[Toggle]) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)
        self.buttons: list[QPushButton] = []
        self._toggles = toggles
        for index, toggle in enumerate(toggles):
            button = QPushButton()
            button.setCheckable(True)
            # Keep clicks from taking focus, so arrow keys don't leave the item grid
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            button.setToolTip(toggle.tooltip)
            button.setProperty("radius", RADIUS)
            button.setFixedSize(MED_HEIGHT, MED_HEIGHT)
            button.setIconSize(_ICON_SIZE)
            set_checked_by_icon(button, by_icon=True)
            edges = Qt.Edge(0)
            if index > 0:
                edges |= Qt.Edge.LeftEdge
            if index < len(toggles) - 1:
                edges |= Qt.Edge.RightEdge
            if edges:
                set_joined_edges(button, edges)
            self.addWidget(button)
            self.buttons.append(button)
        self.set_icons()

    def set_icons(self) -> None:
        """Color icons for the current theme."""
        for button, toggle in zip(self.buttons, self._toggles, strict=True):
            button.setIcon(
                toggle_icon(toggle.svg, toggle.checked_svg, _ICON_SIZE, button.devicePixelRatioF())
            )
