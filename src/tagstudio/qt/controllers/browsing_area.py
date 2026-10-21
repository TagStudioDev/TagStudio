# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from typing import override

from PySide6.QtWidgets import QWidget

from tagstudio.qt.controllers.banner_stack import BannerStack
from tagstudio.qt.controllers.pagination import Pagination
from tagstudio.qt.controllers.thumb_grid import ThumbGrid
from tagstudio.qt.mixed.landing import LandingWidget
from tagstudio.qt.views.browsing_area_view import BrowsingAreaView

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


class BrowsingArea(QWidget):
    """Library browsing area, including item views and notification banners."""

    def __init__(self, driver: QtDriver, pixel_ratio: float) -> None:
        super().__init__()
        self.setObjectName("browsing_area")

        # Pagination floats over the bottom of the results instead of taking up layout space
        self.pagination = Pagination(self)
        self.setLayout(BrowsingAreaView(driver, pixel_ratio, self.pagination))
        self.pagination.raise_()
        self.pagination.index.connect(lambda _: self.thumb_grid.scroll_area.setFocus())

    @override
    def layout(self) -> BrowsingAreaView:
        layout = super().layout()
        assert isinstance(layout, BrowsingAreaView)
        return layout

    @property
    def thumb_grid(self) -> ThumbGrid:
        return self.layout().thumb_grid

    @property
    def banners(self) -> BannerStack:
        return self.layout().banners

    @property
    def landing_widget(self) -> LandingWidget:
        return self.layout().landing_widget

    def toggle_landing_page(self, enabled: bool) -> None:
        view = self.layout()
        if enabled:
            view.thumb_grid.scroll_area.setHidden(True)
            view.landing_widget.setHidden(False)
        else:
            view.landing_widget.setHidden(True)
            view.landing_widget.set_status_label("")
            view.thumb_grid.scroll_area.setHidden(False)
