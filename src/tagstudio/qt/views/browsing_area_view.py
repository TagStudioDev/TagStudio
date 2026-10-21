# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing

from PySide6.QtWidgets import QVBoxLayout

from tagstudio.qt.controllers.banner_stack import BannerStack
from tagstudio.qt.controllers.landing_page import LandingPage
from tagstudio.qt.controllers.pagination import Pagination
from tagstudio.qt.controllers.thumb_grid import ThumbGrid
from tagstudio.qt.views.styles.stylesheets import WIN_PAD

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


class BrowsingAreaView(QVBoxLayout):
    def __init__(self, driver: QtDriver, pixel_ratio: float, pagination: Pagination) -> None:
        super().__init__()
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)

        self.banners = BannerStack()
        self.banners.setContentsMargins(WIN_PAD, 0, 0, 0)
        self.addWidget(self.banners)

        self.thumb_grid = ThumbGrid(driver, pagination)
        # Left padding is part of the grid so box selections can start from it.
        # Bottom padding so floating pagination bar doesn't block bottom of scroll contents.
        self.thumb_grid.setContentsMargins(WIN_PAD, 0, 0, Pagination.HEIGHT)
        self.addWidget(self.thumb_grid.scroll_area)

        self.landing_page = LandingPage(pixel_ratio)
        self.addWidget(self.landing_page)
