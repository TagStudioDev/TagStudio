# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import QSize, QStringListModel, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCompleter,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QToolButton,
)

from tagstudio.i18n.translations import Translations
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import (
    set_svg_icon,
    svg_color_overlay,
    theme_foreground_color,
)
from tagstudio.qt.views.styles.palette import Palette
from tagstudio.qt.views.styles.stylesheets import (
    MED_HEIGHT,
    RADIUS,
    WIN_PAD,
    item_thumb_hover_color,
)
from tagstudio.qt.views.styles.tagstudio_style import line_edit_icon_size, set_joined_edges


class SearchBarView(QHBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setContentsMargins(WIN_PAD, 0, 0, 0)
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(0)
        self.back_button = QPushButton()
        self.back_button.setProperty("radius", RADIUS)
        self.back_button.setObjectName("back_button")
        self.back_button.setFixedSize(QSize(MED_HEIGHT, MED_HEIGHT))
        set_joined_edges(self.back_button, Qt.Edge.RightEdge)
        nav_layout.addWidget(self.back_button)

        self.forward_button = QPushButton()
        self.forward_button.setProperty("radius", RADIUS)
        self.forward_button.setObjectName("forward_button")
        self.forward_button.setFixedSize(QSize(MED_HEIGHT, MED_HEIGHT))
        set_joined_edges(self.forward_button, Qt.Edge.LeftEdge)
        nav_layout.addWidget(self.forward_button)
        self.addLayout(nav_layout)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(Translations["home.search_entries"])
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumSize(QSize(0, MED_HEIGHT))
        self.search_field_completion_list = QStringListModel()
        self.search_field_completer = QCompleter(
            self.search_field_completion_list, self.search_field
        )
        self.search_field_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_field.setCompleter(self.search_field_completer)
        self.options_action = self.search_field.addAction(
            QIcon(), QLineEdit.ActionPosition.TrailingPosition
        )
        self.options_action.setToolTip(Translations["browsing.options"])
        self.options_button = next(
            button
            for button in self.options_action.associatedObjects()
            if isinstance(button, QToolButton)
        )
        self.options_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.options_menu = QMenu()
        self.show_hidden_entries_action = self.options_menu.addAction(
            Translations["home.show_hidden_entries"]
        )
        self.show_hidden_entries_action.setCheckable(True)
        self._is_options_hovered = False
        self._is_options_menu_open = False
        self.addWidget(self.search_field)
        self.set_button_icons()

    def set_button_icons(self) -> None:
        """Color the buttons' icons for the current theme."""
        rm = ResourceManager()
        set_svg_icon(self.back_button, rm.bxs_left_arrow, Palette.contrast())
        set_svg_icon(self.forward_button, rm.bxs_right_arrow, Palette.contrast())
        self.update_options_icon()

    def set_options_hovered(self, hovered: bool) -> None:
        """Set whether the search options icon is hovered."""
        self._is_options_hovered = hovered
        self.update_options_icon()

    def set_options_menu_open(self, is_open: bool) -> None:
        """Set whether the search options menu is open."""
        self._is_options_menu_open = is_open
        self.update_options_icon()

    def update_options_icon(self) -> None:
        """Update the search options icon for its hover and menu state."""
        rm = ResourceManager()
        svg, solid_svg = rm.search_settings_icon, rm.search_settings_icon_solid
        ratio = self.search_field.devicePixelRatioF()
        size = line_edit_icon_size(self.search_field)
        if self._is_options_menu_open:
            svg, color = solid_svg, Palette.accent_alt()
        elif self.show_hidden_entries_action.isChecked():
            color = Palette.accent_alt()
        elif self._is_options_hovered:
            color = item_thumb_hover_color()
        else:
            color = theme_foreground_color()
        icon = QIcon(svg_color_overlay(svg, color, ratio, size))
        icon.addPixmap(
            svg_color_overlay(solid_svg, Palette.accent_alt(), ratio, size), QIcon.Mode.Active
        )
        self.options_action.setIcon(icon)
