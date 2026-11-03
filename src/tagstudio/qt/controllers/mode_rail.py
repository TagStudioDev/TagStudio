# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from typing import override

from PySide6.QtCore import QEvent, QPoint, QRect
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QButtonGroup, QWidget

from tagstudio.qt.views.mode_rail_view import ModeRailView
from tagstudio.qt.views.styles.stylesheets import LARGE_RADIUS, is_dark_theme
from tagstudio.qt.views.styles.widget_effects import SurfaceStyle, WidgetEffects

if typing.TYPE_CHECKING:
    from tagstudio.qt.controllers.menu_bar import MenuBar

_RAISED_DARK = QColor(255, 255, 255, 15)
_RAISED_LIGHT = QColor(255, 255, 255, 140)


class ModeRail(QWidget):
    """A strip of library mode and tool buttons."""

    def __init__(self) -> None:
        super().__init__()
        self.setLayout(ModeRailView())
        self._effect = WidgetEffects()
        # NOTE: Using a QButtonGroup keeps the Entries button checked when clicked again
        self._mode_buttons = QButtonGroup(self)
        self._mode_buttons.addButton(self.layout().entries_button)

    @override
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ThemeChange:
            self.layout().repaint_buttons()
        super().changeEvent(event)

    def set_sync_running(self, running: bool) -> None:
        self.layout().sync_button.set_spinning(running)

    def paint_background(self, painter: QPainter, window_height: int) -> None:
        right = self.mapTo(self.window(), QPoint(self.width(), 0)).x()
        painter.fillRect(
            QRect(0, 0, right, window_height), _RAISED_DARK if is_dark_theme() else _RAISED_LIGHT
        )
        strip = QRect(
            QPoint(-LARGE_RADIUS, -LARGE_RADIUS), QPoint(right - 1, window_height + LARGE_RADIUS)
        )
        self._effect.paint_outlines(painter, strip, LARGE_RADIUS, style=SurfaceStyle.EMBOSSED)

    @override
    def layout(self) -> ModeRailView:
        layout = super().layout()
        assert isinstance(layout, ModeRailView)
        return layout

    def connect_menu_actions(self, menu_bar: MenuBar) -> None:
        view = self.layout()
        # TODO: Switch to the Tags and Colors modes once they exist, instead of opening their modals
        for button, action in (
            (view.tags_button, menu_bar.tag_manager_action),
            (view.colors_button, menu_bar.color_manager_action),
            (view.settings_button, menu_bar.settings_action),
            (view.library_stats_button, menu_bar.library_info_action),
            (view.sync_button, menu_bar.sync_library_action),
        ):
            button.setToolTip(action.iconText())
            button.setEnabled(action.isEnabled())
            action.enabledChanged.connect(button.setEnabled)
            button.clicked.connect(action.trigger)
