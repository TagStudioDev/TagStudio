# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QIcon,
    QPalette,
)
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSlider,
)

from tagstudio.core.library.alchemy.enums import SortingModeEnum
from tagstudio.i18n.translations import Translations
from tagstudio.qt.app_settings import PAGE_SIZES, ShowLabelOption
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import svg_color_overlay, theme_foreground_color
from tagstudio.qt.views.styles.stylesheets import MED_HEIGHT, PAD, RADIUS, WIN_PAD
from tagstudio.qt.views.styles.tagstudio_style import set_joined_edges

_ICON_SIZE = QSize(18, 18)
_SMALL_THUMB_ICON_SIZE = QSize(12, 12)
_LARGE_THUMB_ICON_SIZE = QSize(18, 18)
_THUMB_SIZE_SLIDER_WIDTH = 96


class BrowsingControlsView(QHBoxLayout):
    MIN_THUMB_SIZE = 72
    MAX_THUMB_SIZE = 240
    THUMB_SIZE_STEP = 24
    DEFAULT_THUMB_SIZE = 120

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(WIN_PAD, 0, 0, 0)
        self.setSpacing(PAD)
        rm = ResourceManager()

        self.results_label = QLabel()
        self.results_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.addWidget(self.results_label, stretch=1)

        # Thumbnail Size
        self.thumb_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.thumb_size_slider.setToolTip(Translations["home.thumbnail_size"])
        self.thumb_size_slider.setFixedWidth(_THUMB_SIZE_SLIDER_WIDTH)
        self.thumb_size_slider.setRange(
            0, (self.MAX_THUMB_SIZE - self.MIN_THUMB_SIZE) // self.THUMB_SIZE_STEP
        )
        self.thumb_size_slider.setPageStep(1)
        self.thumb_size_slider.setValue(
            (self.DEFAULT_THUMB_SIZE - self.MIN_THUMB_SIZE) // self.THUMB_SIZE_STEP
        )
        self._small_thumb_icon = QLabel()
        self._large_thumb_icon = QLabel()
        thumb_size_controls = QHBoxLayout()
        thumb_size_controls.setSpacing(PAD)
        thumb_size_controls.addWidget(self._small_thumb_icon)
        thumb_size_controls.addWidget(self.thumb_size_slider)
        thumb_size_controls.addWidget(self._large_thumb_icon)
        self.addLayout(thumb_size_controls)

        # Views
        self.view_button = self._button(Translations["browsing.view"])
        self.view_button.setText(Translations["browsing.view.grid"])
        self.view_options_menu = QMenu(self.view_button)
        self.view_button.setMenu(self.view_options_menu)
        self._view_actions: list[tuple[QAction, bytes]] = []
        self.view_options_menu.addSection(Translations["browsing.view.library"])
        # TODO: Add the other views
        for svg, key in (
            (rm.grid_view_icon, "browsing.view.grid"),
            (rm.masonry_view_icon, "browsing.view.masonry"),
            (rm.list_view_icon, "browsing.view.list"),
            (rm.gallery_view_icon, "browsing.view.gallery"),
        ):
            self._add_view_action(svg, key, is_available=key == "browsing.view.grid")
        self.view_options_menu.addSection(Translations["browsing.view.file_system"])
        self._add_view_action(rm.file_system_icons_view_icon, "browsing.view.file_system_icons")
        self._add_view_action(rm.file_system_list_view_icon, "browsing.view.file_system_list")
        self.view_options_menu.addSeparator()
        self.show_filenames_action = self.view_options_menu.addAction(
            Translations["settings.show_filenames_in_grid"]
        )
        self.show_filenames_action.setCheckable(True)
        self.show_extensions_menu = self._add_show_label_menu(
            Translations["settings.show_extensions_in_grid"]
        )
        self.show_durations_menu = self._add_show_label_menu(
            Translations["settings.show_durations_in_grid"]
        )
        self.view_options_menu.addSeparator()
        self.infinite_scroll_action = self.view_options_menu.addAction(
            Translations["settings.infinite_scroll"]
        )
        self.infinite_scroll_action.setCheckable(True)
        self.page_size_menu = self.view_options_menu.addMenu(Translations["settings.page_size"])
        self.page_size_group = QActionGroup(self.page_size_menu)
        for page_size in PAGE_SIZES:
            action = self.page_size_menu.addAction(str(page_size))
            action.setCheckable(True)
            action.setData(page_size)
            self.page_size_group.addAction(action)
        self.addWidget(self.view_button)

        # Sorting
        self.sort_direction_button = self._button("")
        self.sort_direction_button.setFixedWidth(MED_HEIGHT)
        set_joined_edges(self.sort_direction_button, Qt.Edge.RightEdge)
        self.sort_mode_combobox = QComboBox()
        self.sort_mode_combobox.setToolTip(Translations["browsing.sort_by"])
        self.sort_mode_combobox.setProperty("radius", RADIUS)
        self.sort_mode_combobox.setFixedHeight(MED_HEIGHT)
        set_joined_edges(self.sort_mode_combobox, Qt.Edge.LeftEdge)
        for mode in SortingModeEnum:
            self.sort_mode_combobox.addItem(Translations[mode.value], mode)
        sort_controls = QHBoxLayout()
        sort_controls.setSpacing(0)
        sort_controls.addWidget(self.sort_direction_button)
        sort_controls.addWidget(self.sort_mode_combobox)
        self.addLayout(sort_controls)

        self.set_icons()

    def set_icons(self) -> None:
        """Color icons for the current theme."""
        rm = ResourceManager()
        alphabetical = (rm.sort_alphabetical_ascending_icon, rm.sort_alphabetical_descending_icon)
        calendar = (rm.sort_calendar_ascending_icon, rm.sort_calendar_descending_icon)
        self.sort_direction_icons: dict[SortingModeEnum, tuple[QIcon, QIcon]] = {
            mode: (self._icon(ascending), self._icon(descending))
            for mode, (ascending, descending) in {
                SortingModeEnum.DATE_ADDED: calendar,
                SortingModeEnum.DATE_CREATED: calendar,
                SortingModeEnum.DATE_MODIFIED: calendar,
                SortingModeEnum.FILE_NAME: alphabetical,
                SortingModeEnum.FILE_SIZE: (
                    rm.sort_numeric_ascending_icon,
                    rm.sort_numeric_descending_icon,
                ),
                SortingModeEnum.PATH: alphabetical,
                SortingModeEnum.RANDOM: (rm.sort_random_icon, rm.sort_random_icon),
            }.items()
        }
        self.view_button.setIcon(self._icon(rm.grid_view_icon))
        for action, svg in self._view_actions:
            action.setIcon(self._icon(svg))
        pixel_ratio = self.results_label.devicePixelRatioF()
        color = theme_foreground_color()
        for label, size in (
            (self._small_thumb_icon, _SMALL_THUMB_ICON_SIZE),
            (self._large_thumb_icon, _LARGE_THUMB_ICON_SIZE),
        ):
            label.setPixmap(svg_color_overlay(rm.preview_icon_solid, color, pixel_ratio, size))

    def _add_view_action(self, svg: bytes, key: str, is_available: bool = False) -> None:
        action = self.view_options_menu.addAction(Translations[key])
        self._view_actions.append((action, svg))
        action.setCheckable(True)
        action.setChecked(is_available)
        action.setEnabled(is_available)

    def _add_show_label_menu(self, title: str) -> QMenu:
        menu = self.view_options_menu.addMenu(title)
        group = QActionGroup(menu)
        for option, key in (
            (ShowLabelOption.ALWAYS, "settings.show_label.option.always"),
            (ShowLabelOption.ON_HOVER, "settings.show_label.option.on_hover"),
            (ShowLabelOption.NEVER, "settings.show_label.option.never"),
        ):
            action = menu.addAction(Translations[key])
            action.setCheckable(True)
            action.setData(option)
            group.addAction(action)
        return menu

    def _button(self, tooltip: str) -> QPushButton:
        button = QPushButton()
        button.setToolTip(tooltip)
        button.setProperty("radius", RADIUS)
        button.setFixedHeight(MED_HEIGHT)
        button.setIconSize(_ICON_SIZE)
        return button

    def _icon(self, svg: bytes) -> QIcon:
        color = self.results_label.palette().color(
            QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText
        )
        pixel_ratio = self.results_label.devicePixelRatioF()
        return QIcon(svg_color_overlay(svg, color, pixel_ratio, _ICON_SIZE))
