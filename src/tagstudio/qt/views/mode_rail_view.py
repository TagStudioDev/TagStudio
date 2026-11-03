# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtWidgets import QVBoxLayout

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.flat_button import FlatButton
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.stylesheets import PAD, WIN_PAD


class ModeRailView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(PAD, 0, PAD, WIN_PAD)
        self.setSpacing(PAD)
        rm = ResourceManager()
        self._buttons: list[FlatButton] = []

        self.entries_button = self._add_button(rm.entries_icon, rm.entries_icon_solid)
        self.entries_button.setToolTip(Translations["mode.entries"])
        self.entries_button.setCheckable(True)
        self.entries_button.setChecked(True)
        self.tags_button = self._add_button(rm.tags_icon, rm.tags_icon_solid)
        self.colors_button = self._add_button(rm.colors_icon, rm.colors_icon_solid)
        self.addStretch(1)

        self.sync_button = self._add_button(rm.sync_icon, rm.sync_icon)
        self.library_stats_button = self._add_button(
            rm.library_stats_icon, rm.library_stats_icon_solid
        )
        self.settings_button = self._add_button(rm.settings_icon, rm.settings_icon_solid)

    def _add_button(self, svg: bytes, solid_svg: bytes) -> FlatButton:
        button = FlatButton(svg, solid_svg)
        self._buttons.append(button)
        self.addWidget(button)
        return button

    def repaint_buttons(self) -> None:
        for button in self._buttons:
            button.update()
