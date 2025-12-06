# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

import structlog
from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.library.alchemy.enums import SortingModeEnum
from tagstudio.qt.controllers.preview_panel_controller import PreviewPanel
from tagstudio.qt.mixed.landing import LandingWidget
from tagstudio.qt.mixed.pagination import Pagination
from tagstudio.qt.views.widgets.search_bar_view import SearchBarWidget
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.thumb_grid_layout import ThumbGridLayout
from tagstudio.qt.views.widgets.main_menu_bar_view import MainMenuBar
from tagstudio.qt.views.widgets.content_display_toolbar_view import ContentDisplayToolbar

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


logger = structlog.get_logger(__name__)

# View Component
class MainWindow(QMainWindow):
    def __init__(self, driver: "QtDriver", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.rm = ResourceManager()

        # region Type declarations for variables that will be initialized in methods
        # initialized in setup_search_bar
        self.search_bar: SearchBarWidget

        # initialized in setup_content_display_toolbar
        self.content_display_toolbar: ContentDisplayToolbar

        # initialized in setup_content
        self.content_layout: QHBoxLayout
        self.content_splitter: QSplitter

        # initialized in setup_entry_list
        self.entry_list_container: QWidget
        self.entry_list_layout: QVBoxLayout
        self.entry_scroll_area: QScrollArea
        self.thumb_grid: QWidget
        self.thumb_layout: ThumbGridLayout
        self.landing_widget: LandingWidget
        self.pagination: Pagination

        # initialized in setup_preview_panel
        self.preview_panel: PreviewPanel
        # endregion

        if not self.objectName():
            self.setObjectName("MainWindow")
        self.resize(1316, 740)

        self.setup_menu_bar()

        self.setup_central_widget(driver)

        self.setup_status_bar()

        QMetaObject.connectSlotsByName(self)

        # NOTE: These are old attempts to allow for a translucent/acrylic
        # window effect. This may be attempted again in the future.
        # self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        # self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
        # # self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # self.windowFX = WindowEffect()
        # self.windowFX.setAcrylicEffect(self.winId(), isEnableShadow=False)

    # region UI Setup Methods

    # region Menu Bar

    def setup_menu_bar(self):
        self.menu_bar = MainMenuBar(self)

        self.setMenuBar(self.menu_bar)
        self.menu_bar.setNativeMenuBar(True)

    # endregion

    def setup_central_widget(self, driver: "QtDriver"):
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")
        self.central_layout = QGridLayout(self.central_widget)
        self.central_layout.setObjectName("central_layout")

        self.setup_search_bar()
        self.setup_content_display_toolbar()
        self.setup_content(driver)
        self.setCentralWidget(self.central_widget)

    def setup_search_bar(self):
        self.search_bar = SearchBarWidget(self.central_widget)
        # Restrict the size, as otherwise the widget will expand vertically.
        self.search_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.central_layout.addWidget(self.search_bar, 3, 0, 1, 1)

    def setup_content_display_toolbar(self):
        """Sets up inputs for sorting settings and thumbnail size."""
        self.content_display_toolbar = ContentDisplayToolbar(self)
        self.content_display_toolbar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.central_layout.addWidget(self.content_display_toolbar, 5, 0, 1, 1)

    def setup_content(self, driver: "QtDriver"):
        self.content_layout = QHBoxLayout()
        self.content_layout.setObjectName("content_layout")

        self.content_splitter = QSplitter()
        self.content_splitter.setObjectName("content_splitter")
        self.content_splitter.setHandleWidth(12)

        self.setup_entry_list(driver)
        self.setup_preview_panel(driver)

        self.content_splitter.setStretchFactor(0, 1)
        self.content_layout.addWidget(self.content_splitter)

        self.central_layout.addLayout(self.content_layout, 10, 0, 1, 1)

    def setup_entry_list(self, driver: "QtDriver"):
        self.entry_list_container = QWidget()
        self.entry_list_layout = QVBoxLayout(self.entry_list_container)
        self.entry_list_layout.setSpacing(0)

        self.entry_scroll_area = QScrollArea()
        self.entry_scroll_area.setObjectName("entry_scroll_area")
        self.entry_scroll_area.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.entry_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.entry_scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.entry_scroll_area.setWidgetResizable(True)
        self.entry_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.entry_scroll_area.verticalScrollBar().valueChanged.connect(
            lambda value: self.thumb_layout.update()
        )

        self.thumb_grid = QWidget()
        self.thumb_grid.setObjectName("thumb_grid")
        self.thumb_layout = ThumbGridLayout(driver, self.entry_scroll_area)
        self.thumb_layout.setSpacing(min(self.thumb_size // 10, 12))
        self.thumb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_grid.setLayout(self.thumb_layout)
        self.entry_scroll_area.setWidget(self.thumb_grid)

        self.entry_list_layout.addWidget(self.entry_scroll_area)

        self.landing_widget = LandingWidget(driver, self.devicePixelRatio())
        self.entry_list_layout.addWidget(self.landing_widget)

        self.pagination = Pagination()
        self.entry_list_layout.addWidget(self.pagination)
        self.content_splitter.addWidget(self.entry_list_container)

    def setup_preview_panel(self, driver: "QtDriver"):
        self.preview_panel = PreviewPanel(driver.lib, driver)
        self.content_splitter.addWidget(self.preview_panel)

    def setup_status_bar(self):
        self.status_bar = QStatusBar(self)
        self.status_bar.setObjectName("status_bar")
        status_bar_size_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        status_bar_size_policy.setHorizontalStretch(0)
        status_bar_size_policy.setVerticalStretch(0)
        status_bar_size_policy.setHeightForWidth(self.status_bar.sizePolicy().hasHeightForWidth())
        self.status_bar.setSizePolicy(status_bar_size_policy)
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)

    # endregion

    def toggle_landing_page(self, enabled: bool):
        if enabled:
            self.entry_scroll_area.setHidden(True)
            self.landing_widget.setHidden(False)
            self.landing_widget.animate_logo_in()
        else:
            self.landing_widget.setHidden(True)
            self.landing_widget.set_status_label("")
            self.entry_scroll_area.setHidden(False)

    @property
    def sorting_mode(self) -> SortingModeEnum:
        """What to sort by."""
        return self.content_display_toolbar.sorting_mode_combobox.currentData()

    @property
    def sorting_direction(self) -> bool:
        """Whether to Sort the results in ascending order."""
        return self.content_display_toolbar.sorting_direction_combobox.currentData()

    @property
    def thumb_size(self) -> int:
        return self.content_display_toolbar.thumb_size_combobox.currentData()

    @property
    def show_hidden_entries(self) -> bool:
        """Whether to show entries tagged with hidden tags."""
        return self.content_display_toolbar.show_hidden_entries_checkbox.isChecked()
