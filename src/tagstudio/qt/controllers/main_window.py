# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
import typing
from typing import override

import structlog
from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QMainWindow, QWidget

from tagstudio.core.library.alchemy.enums import SortingModeEnum
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.browsing_area import BrowsingArea
from tagstudio.qt.controllers.inspector import Inspector
from tagstudio.qt.controllers.menu_bar import MenuBar
from tagstudio.qt.controllers.search_bar import SearchBar
from tagstudio.qt.controllers.thumb_grid import ThumbGrid
from tagstudio.qt.mixed.drop_import_modal import DropImportModal
from tagstudio.qt.views.main_window_view import MainWindowView

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


logger = structlog.get_logger(__name__)


class MainWindow(QMainWindow):
    navigation_requested = Signal(int)
    sorting_mode_changed = Signal(SortingModeEnum)
    sorting_direction_changed = Signal(bool)
    show_hidden_entries_changed = Signal(bool)

    def __init__(self, driver: QtDriver, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._driver = driver

        self.setObjectName("main_window")
        self.resize(1280, 720)

        self.menu_bar = MenuBar(driver, self)
        self.setMenuBar(self.menu_bar)
        self.menu_bar.setNativeMenuBar(True)

        central_widget = QWidget(self)
        central_widget.setObjectName("central_widget")
        central_widget.setLayout(MainWindowView(driver, self.devicePixelRatio()))
        self.setCentralWidget(central_widget)

        self._connect_callbacks()
        self.toggle_landing_page(enabled=True)

    @override
    def layout(self) -> MainWindowView:
        # NOTE: Returns the built-in centralWidget's view, not the QMainWindow's own layout
        layout = unwrap(self.centralWidget()).layout()
        assert isinstance(layout, MainWindowView)
        return layout

    def _connect_callbacks(self) -> None:
        self.menu_bar.increase_thumbnail_size_action.triggered.connect(self.increase_thumb_size)
        self.menu_bar.decrease_thumbnail_size_action.triggered.connect(self.decrease_thumb_size)

        view = self.layout()
        view.search_bar.navigation_requested.connect(self.navigation_requested)
        view.sorting_mode_combobox.currentIndexChanged.connect(
            lambda: self.sorting_mode_changed.emit(self.sorting_mode)
        )
        view.sorting_direction_combobox.currentIndexChanged.connect(
            lambda: self.sorting_direction_changed.emit(self.sorting_direction)
        )
        view.show_hidden_entries_checkbox.stateChanged.connect(
            lambda: self.show_hidden_entries_changed.emit(self.show_hidden_entries)
        )
        view.thumb_size_combobox.currentIndexChanged.connect(
            lambda: self.thumb_grid.set_thumb_size(self.thumb_size)
        )
        view.content_splitter.splitterMoved.connect(lambda *_: self._snap_content_splitter())
        self.thumb_grid.scroll_area.installEventFilter(self)

    @property
    def search_bar(self) -> SearchBar:
        return self.layout().search_bar

    @property
    def browsing_area(self) -> BrowsingArea:
        return self.layout().browsing_area

    @property
    def thumb_grid(self) -> ThumbGrid:
        return self.layout().browsing_area.thumb_grid

    @property
    def inspector(self) -> Inspector:
        return self.layout().inspector

    @property
    def sorting_mode(self) -> SortingModeEnum:
        """What to sort by."""
        return self.layout().sorting_mode_combobox.currentData()

    @property
    def sorting_direction(self) -> bool:
        """Whether to sort the results in ascending order."""
        return self.layout().sorting_direction_combobox.currentData()

    @property
    def thumb_size(self) -> int:
        return self.layout().thumb_size_combobox.currentData()

    @property
    def show_hidden_entries(self) -> bool:
        """Whether to show entries tagged with hidden tags."""
        return self.layout().show_hidden_entries_checkbox.isChecked()

    def toggle_landing_page(self, enabled: bool) -> None:
        """Show the landing page and hide any library controls and panels."""
        view = self.layout()
        view.search_bar.setHidden(enabled)
        view.extra_input_bar.setHidden(enabled)
        view.inspector.setHidden(enabled)
        view.browsing_area.toggle_landing_page(enabled)

    def set_sorting_mode(self, mode: SortingModeEnum) -> None:
        self.layout().sorting_mode_combobox.setCurrentIndex(list(SortingModeEnum).index(mode))

    def set_results_text(self, text: str) -> None:
        self.layout().results_label.setText(text)

    def increase_thumb_size(self) -> None:
        combobox = self.layout().thumb_size_combobox
        new_val = combobox.currentIndex() - 1
        if not new_val < 0:
            combobox.setCurrentIndex(new_val)

    def decrease_thumb_size(self) -> None:
        combobox = self.layout().thumb_size_combobox
        new_val = combobox.currentIndex() + 1
        if not (new_val + 1) > len(MainWindowView.THUMB_SIZES):
            combobox.setCurrentIndex(new_val)

    def _snap_content_splitter(self) -> None:
        """Snap the splitter so it fits a whole number of thumbnail grid columns."""
        if not self.thumb_grid.isVisible():
            return
        view = self.layout()
        grid_width = self.thumb_grid.layout().geometry().width()
        cell_width = self.thumb_grid.layout().cell_width()
        grid_size, inspector_size = view.content_splitter.sizes()
        if inspector_size == 0:  # Collapsed by dragging the splitter all the way
            return
        columns = max(1, round(grid_width / cell_width))
        # Round down when the Inspector can't shrink enough to fit another column
        if (
            inspector_size + grid_width - columns * cell_width
            < self.inspector.minimumSizeHint().width()
        ):
            columns = max(1, grid_width // cell_width)
        # Round up when the grid's side can't shrink enough to lose a column
        elif (
            grid_size - grid_width + columns * cell_width
            < view.central_content.minimumSizeHint().width()
        ):
            columns = math.ceil(grid_width / cell_width)
        extra = grid_width - columns * cell_width
        if extra:
            view.content_splitter.setSizes([grid_size - extra, inspector_size + extra])

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # Snap once the grid has been laid out
        if watched is self.thumb_grid.scroll_area and event.type() == QEvent.Type.Show:
            QTimer.singleShot(0, self._snap_content_splitter)
        return super().eventFilter(watched, event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.ForwardButton:
            self.navigation_requested.emit(1)
        elif event.button() == Qt.MouseButton.BackButton:
            self.navigation_requested.emit(-1)
        else:
            super().mousePressEvent(event)

    @override
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @override
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @override
    def dropEvent(self, event: QDropEvent) -> None:
        if event.source() is self._driver:
            return

        if not event.mimeData().hasUrls():
            return

        urls = event.mimeData().urls()
        logger.info("[MainWindow] New items dragged in", urls=urls)
        drop_import = DropImportModal(self._driver)
        drop_import.import_urls(urls)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.menu_bar.clear_select_action.trigger()
        return super().keyPressEvent(event)
