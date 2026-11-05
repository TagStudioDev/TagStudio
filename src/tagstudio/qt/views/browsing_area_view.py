# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing

from PySide6.QtWidgets import QVBoxLayout

from tagstudio.qt.controllers.banner_stack import BannerStack
from tagstudio.qt.controllers.landing_page import LandingPage
from tagstudio.qt.controllers.pagination import Pagination
from tagstudio.qt.controllers.thumb_grid import ThumbGrid
from tagstudio.qt.views.styles.stylesheets import WIN_PAD
from tagstudio.qt.views.styles.tagstudio_style import set_track_inset
from tagstudio.qt.views.styles.widget_effects import DEBOSSED_OUTLINE_WIDTH

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


_SCROLL_TRACK_INSET = 3


class BrowsingAreaView(QVBoxLayout):
    def __init__(self, driver: QtDriver, pixel_ratio: float, pagination: Pagination) -> None:
        super().__init__()
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)

        self.banners = BannerStack()
        self.banners.setContentsMargins(WIN_PAD, 0, 0, 0)
        self.addWidget(self.banners)
        self.addSpacing(DEBOSSED_OUTLINE_WIDTH)

        self.thumb_grid = ThumbGrid(driver, pagination)
        # Left and top padding are part of the grid so box selections can start from them.
        # Bottom padding so floating pagination bar doesn't block bottom of scroll contents.
        # Negative right padding puts the last column's spacing under the scroll bar.
        spacing = self.thumb_grid.layout().spacing()
        self.thumb_grid.setContentsMargins(WIN_PAD, WIN_PAD, -spacing, Pagination.HEIGHT)
        set_track_inset(self.thumb_grid.scroll_area.verticalScrollBar(), _SCROLL_TRACK_INSET)
        self.addWidget(self.thumb_grid.scroll_area)

        self.landing_page = LandingPage(pixel_ratio)
        self.addWidget(self.landing_page)
