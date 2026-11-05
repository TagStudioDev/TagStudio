# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from typing import cast, override

import structlog
from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QRect,
    QSignalBlocker,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
)
from PySide6.QtWidgets import QMainWindow, QWidget

from tagstudio.core.library.alchemy.enums import SortingModeEnum
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.browsing_area import BrowsingArea
from tagstudio.qt.controllers.inspector import Inspector
from tagstudio.qt.controllers.menu_bar import MenuBar
from tagstudio.qt.controllers.search_bar import SearchBar
from tagstudio.qt.controllers.size_animation import DURATION
from tagstudio.qt.controllers.splitter_corner_handle import SplitterCornerHandle
from tagstudio.qt.controllers.tagging_panel import TaggingPanel
from tagstudio.qt.controllers.thumb_grid import ThumbGrid
from tagstudio.qt.mixed.drop_import_modal import DropImportModal
from tagstudio.qt.views.main_window_view import MainWindowView, SidePanelToggle
from tagstudio.qt.views.styles.stylesheets import (
    LARGE_RADIUS,
    MED_HEIGHT,
    PAD,
    WIN_PAD,
)
from tagstudio.qt.views.styles.tagstudio_style import (
    set_at_limit,
    set_handle_span,
    set_shown_at_rest,
    set_track_side_inset,
)
from tagstudio.qt.views.styles.widget_effects import (
    DEBOSSED_OUTLINE_WIDTH,
    SurfaceStyle,
    WidgetEffects,
)

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


logger = structlog.get_logger(__name__)

_CLOSED_SEARCH_BAR_INSET = MED_HEIGHT + PAD  # Side panel button room


class MainWindow(QMainWindow):
    navigation_requested = Signal(int)
    sorting_mode_changed = Signal(SortingModeEnum)
    sorting_direction_changed = Signal(bool)
    show_hidden_entries_changed = Signal(bool)
    pagination_changed = Signal(bool, int)  # (Infinite Scroll, Page Size)
    filenames_visible_changed = Signal(bool)

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
        content_splitter = self.layout().content_splitter
        set_handle_span(content_splitter, *MainWindowView.PANEL_HANDLE_INSETS)
        set_shown_at_rest(content_splitter, shown=False)
        set_track_side_inset(
            self.thumb_grid.scroll_area.verticalScrollBar(), DEBOSSED_OUTLINE_WIDTH
        )
        for index in range(content_splitter.count()):
            content_splitter.setCollapsible(index, False)  # noqa: FBT003
        self._painted_surface_top: int | None = None
        self._content_handle_width = content_splitter.handleWidth()
        self._side_handle_width = self.layout().side_splitter.handleWidth()
        self._no_max_width = self.layout().tagging_panel.maximumWidth()
        self._is_side_open = True
        self._side_width = 0
        self._side_total_width = 0.0
        self._side_animation = self._panel_animation()
        self._side_animation.valueChanged.connect(self._set_side_total_width)
        self._side_animation.finished.connect(self._finish_side_animation)
        self._is_inspector_open = True
        self._is_tagging_open = False
        # Inspector and tagging tools widths
        self._column_widths = [0.0, 0.0]
        self._column_start_widths = [0.0, 0.0]
        self._column_end_widths = [0.0, 0.0]
        self._open_column_widths = [
            self.inspector.sizeHint().width(),
            self.layout().tagging_panel.sizeHint().width(),
        ]
        self._columns_animation = self._panel_animation()
        self._columns_animation.valueChanged.connect(self._set_columns_progress)
        self._columns_animation.finished.connect(self._finish_columns_animation)
        side_panel_button = self.layout().side_panel_button
        side_panel_button.setParent(central_widget)
        side_panel_button.raise_()
        self._corner_handle = SplitterCornerHandle(
            self.layout().content_splitter,
            self.inspector.preview_splitter,
            self._corner_handle_content_widget,
            central_widget,
        )

        self._connect_callbacks()
        view = self.layout()
        view.inspector_toggles.set_checked(SidePanelToggle.FILE_INFO, checked=True)
        view.inspector_toggles.set_checked(SidePanelToggle.PREVIEW, checked=True)
        view.inspector_toggles.set_checked(SidePanelToggle.TAGS_AND_FIELDS, checked=True)
        self.toggle_landing_page(enabled=True)

    def _panel_animation(self) -> QVariantAnimation:
        animation = QVariantAnimation(self)
        animation.setDuration(DURATION)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        if self.browsing_area.landing_page.isVisible():
            content_top = unwrap(self.centralWidget()).y()
            self.browsing_area.landing_page.background.paint(painter, self.rect(), content_top)
        else:
            rail = self.layout().mode_rail
            if rail.isVisible():
                rail.paint_background(painter, self.height())
                painter.setClipRect(
                    QRect(
                        rail.mapTo(self, QPoint(rail.width(), 0)).x(),
                        0,
                        self.width(),
                        self.height(),
                    )
                )
            self._paint_browsing_surface(painter)
        painter.end()

    def _browsing_surface_rect(self) -> QRect:
        """The rect of the browsing area's surface."""

        def panel_edge_x() -> float:
            return self.layout().content_splitter.handle(1).mapTo(self, QPoint(0, 0)).x()

        top = self.thumb_grid.scroll_area.mapTo(self, QPoint(0, 0)).y() - DEBOSSED_OUTLINE_WIDTH
        right = self.width() + LARGE_RADIUS
        if self.layout().side_panel.isVisible():
            right = round(panel_edge_x())
        return QRect(QPoint(-LARGE_RADIUS, top), QPoint(right - 1, self.height() + LARGE_RADIUS))

    def _paint_browsing_surface(self, painter: QPainter) -> None:
        """Paint the browsing area's surface."""
        surface = self._browsing_surface_rect()
        self._painted_surface_top = surface.top()
        WidgetEffects().paint_surface(painter, surface, LARGE_RADIUS, style=SurfaceStyle.DEBOSSED)

    def _update_surface_top(self) -> None:
        """Update the surface's top edges.

        NOTE: This is only here to cover a strange edge case where the top of the thumbnail grid
        doesn't get repainted after a banner has animated in/out and moved the grid.
        """
        new_top = self._browsing_surface_rect().top()
        for top in {self._painted_surface_top, new_top}:
            if top is not None:
                self.update(QRect(0, top, self.width(), LARGE_RADIUS + DEBOSSED_OUTLINE_WIDTH))

    @override
    def layout(self) -> MainWindowView:
        # NOTE: Returns the built-in centralWidget's view, not the QMainWindow's own layout
        layout = unwrap(self.centralWidget()).layout()
        assert isinstance(layout, MainWindowView)
        return layout

    def _connect_callbacks(self) -> None:
        self.browsing_area.landing_page.background_changed.connect(self.update)

        view = self.layout()
        controls = view.browsing_controls
        self.menu_bar.increase_thumbnail_size_action.triggered.connect(controls.increase_thumb_size)
        self.menu_bar.decrease_thumbnail_size_action.triggered.connect(controls.decrease_thumb_size)
        self.menu_bar.tagging_panel_action.triggered.connect(self._toggle_tagging_panel)
        view.mode_rail.connect_menu_actions(self.menu_bar)
        view.inspector_toggles.toggled.connect(self._on_inspector_toggled)
        view.side_panel_button.clicked.connect(self._toggle_side_panel)
        unwrap(self.centralWidget()).installEventFilter(self)
        view.search_bar.layout().search_field.installEventFilter(self)
        view.search_bar.navigation_requested.connect(self.navigation_requested)
        view.search_bar.show_hidden_entries_changed.connect(self.show_hidden_entries_changed)
        controls.sorting_mode_changed.connect(self.sorting_mode_changed)
        controls.sorting_direction_changed.connect(self.sorting_direction_changed)
        controls.thumb_size_changed.connect(self.thumb_grid.set_thumb_size)
        controls.pagination_changed.connect(self.pagination_changed)
        controls.filenames_visible_changed.connect(self.filenames_visible_changed)
        view.content_splitter.splitterMoved.connect(self._update_content_splitter_limit)
        view.content_splitter.splitterMoved.connect(self.update)
        view.content_splitter.handle(1).installEventFilter(self)
        self._driver.selection.changed.connect(self._corner_handle.queue_update)
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
    def tagging_panel(self) -> TaggingPanel:
        return self.layout().tagging_panel

    @property
    def sorting_mode(self) -> SortingModeEnum:
        """What to sort by."""
        return self.layout().browsing_controls.sorting_mode

    @property
    def sorting_direction(self) -> bool:
        """Whether to sort the results in ascending order."""
        return self.layout().browsing_controls.sorting_direction

    @property
    def thumb_size(self) -> int:
        return self.layout().browsing_controls.thumb_size

    @property
    def show_hidden_entries(self) -> bool:
        """Whether to show entries tagged with "is_hidden" tags."""
        return self.layout().search_bar.show_hidden_entries

    def toggle_landing_page(self, enabled: bool) -> None:
        """Show the landing page and hide any library controls and panels."""
        view = self.layout()
        view.mode_rail.setHidden(enabled)
        view.search_bar.setHidden(enabled)
        view.browsing_controls.setHidden(enabled)
        view.side_panel.setHidden(enabled or not self._is_side_open)
        view.side_panel_button.setHidden(enabled)
        view.browsing_area.toggle_landing_page(enabled)

    def _on_inspector_toggled(self, index: int, shown: bool) -> None:
        toggles = self.layout().inspector_toggles
        is_inspector_open = any(toggles.is_checked(i) for i in range(SidePanelToggle.TAGGING_PANEL))
        is_tagging_open = toggles.is_checked(SidePanelToggle.TAGGING_PANEL)
        if not is_inspector_open and not is_tagging_open:
            with QSignalBlocker(toggles):
                toggles.set_checked(index, checked=True)
            self._set_side_panel_open(is_open=False)
            return

        if index == SidePanelToggle.FILE_INFO:
            self.inspector.set_file_info_shown(shown)
        elif index == SidePanelToggle.PREVIEW:
            self.inspector.set_preview_shown(shown)
        elif index == SidePanelToggle.TAGS_AND_FIELDS:
            self.inspector.set_tags_fields_shown(shown)
        if (is_inspector_open, is_tagging_open) != (self._is_inspector_open, self._is_tagging_open):
            self._is_inspector_open = is_inspector_open
            self._is_tagging_open = is_tagging_open
            self._animate_side_columns()

    def _animate_side_columns(self) -> None:
        """Animate the Inspector and tagging panel open or closed."""
        view = self.layout()
        columns = (view.inspector, view.tagging_panel)
        if self._columns_animation.state() != QAbstractAnimation.State.Running:
            self._column_widths = [float(c.width()) if c.isVisible() else 0.0 for c in columns]
            for index, width in enumerate(self._column_widths):
                if width > 0:
                    self._open_column_widths[index] = round(width)
        self._columns_animation.stop()
        self._column_start_widths = self._column_widths
        self._column_end_widths = [
            float(self._open_column_widths[0]) if self._is_inspector_open else 0.0,
            float(self._open_column_widths[1]) if self._is_tagging_open else 0.0,
        ]
        if self._is_inspector_open and self._is_tagging_open:
            room = (
                sum(view.content_splitter.sizes())
                - view.central_content.minimumSizeHint().width()
                - self._side_handle_width
                - WIN_PAD
            )
            self._column_end_widths[0] = max(
                float(view.inspector.minimumSizeHint().width()),
                min(self._column_end_widths[0], room - self._column_end_widths[1]),
            )
        self._set_column_widths(self._column_start_widths)
        for column in columns:
            column.setHidden(False)
        if not self.isVisible():
            self._set_column_widths(self._column_end_widths)
            self._finish_columns_animation()
            return
        with QSignalBlocker(self._columns_animation):
            self._columns_animation.setStartValue(0.0)
            self._columns_animation.setEndValue(1.0)
        self._columns_animation.start()

    def _set_columns_progress(self, progress: float) -> None:
        self._set_column_widths(
            [
                start + (end - start) * progress
                for start, end in zip(
                    self._column_start_widths, self._column_end_widths, strict=True
                )
            ]
        )

    def _set_column_widths(self, widths: list[float]) -> None:
        """Set the Inspector and tagging panel's widths."""
        self._column_widths = widths
        view = self.layout()
        inspector_width, tagging_width = (round(width) for width in widths)
        handle_width = min(inspector_width, tagging_width, self._side_handle_width)
        view.side_splitter.setHandleWidth(handle_width)
        view.inspector.setFixedWidth(inspector_width)  # Keeps text from rewrapping
        view.tagging_panel.setMaximumWidth(tagging_width)
        view.side_splitter.refresh()
        side_width = inspector_width + handle_width + tagging_width + WIN_PAD
        view.content_splitter.setSizes(
            [sum(view.content_splitter.sizes()) - side_width, side_width]
        )
        view.side_splitter.setSizes([inspector_width, tagging_width])
        self.update()

    def _finish_columns_animation(self) -> None:
        view = self.layout()
        view.inspector.setHidden(not self._is_inspector_open)
        view.tagging_panel.setHidden(not self._is_tagging_open)
        view.side_splitter.setHandleWidth(self._side_handle_width)
        view.inspector.setMinimumWidth(0)
        view.inspector.setMaximumWidth(self._no_max_width)
        view.tagging_panel.setMaximumWidth(self._no_max_width)

    def _toggle_tagging_panel(self) -> None:
        """Toggle the tagging panel and focus its tag search when it opens."""
        view = self.layout()
        if self._is_side_open and self._is_tagging_open:
            view.inspector_toggles.set_checked(SidePanelToggle.TAGGING_PANEL, checked=False)
            return
        view.inspector_toggles.set_checked(SidePanelToggle.TAGGING_PANEL, checked=True)
        if not self._is_side_open:
            self._set_side_panel_open(is_open=True)
        view.tagging_panel.focus_tag_search()

    def _toggle_side_panel(self) -> None:
        self._set_side_panel_open(not self._is_side_open)

    def _set_side_panel_open(self, is_open: bool) -> None:
        """Set whether the side panel is open."""
        view = self.layout()
        self._is_side_open = is_open
        view.side_panel_button.setChecked(is_open)
        unwrap(view.side_panel.layout()).setEnabled(False)
        if self._side_animation.state() != QAbstractAnimation.State.Running:
            is_visible = view.side_panel.isVisible()
            if is_visible:
                self._side_width = view.content_splitter.sizes()[1]
            else:
                view.side_contents.setGeometry(
                    0, 0, self._side_width - WIN_PAD, view.content_splitter.height()
                )
            self._side_total_width = float(
                self._side_width + self._content_handle_width if is_visible else 0
            )
        self._side_animation.stop()
        end = float(self._side_width + self._content_handle_width if is_open else 0)
        self._set_side_total_width(self._side_total_width)
        view.side_panel.setHidden(False)
        if not self.isVisible():
            self._set_side_total_width(end)
            self._finish_side_animation()
            return
        with QSignalBlocker(self._side_animation):
            self._side_animation.setStartValue(self._side_total_width)
            self._side_animation.setEndValue(end)
        self._side_animation.start()

    def _set_side_total_width(self, total_width: float) -> None:
        """Set the combined width of the side panel and its handle."""
        self._side_total_width = total_width
        view = self.layout()
        rounded_width = round(total_width)
        handle_width = min(rounded_width, self._content_handle_width)
        view.content_splitter.setHandleWidth(handle_width)
        side_width = rounded_width - handle_width
        view.side_panel.setMaximumWidth(side_width)
        view.content_splitter.setSizes(
            [sum(view.content_splitter.sizes()) - side_width, side_width]
        )
        search_bar_layout = view.search_bar.layout()
        search_bar_layout.setContentsMargins(
            WIN_PAD, 0, max(0, _CLOSED_SEARCH_BAR_INSET - rounded_width), 0
        )
        search_bar_layout.activate()
        controls_layout = view.browsing_controls.layout()
        controls_layout.setContentsMargins(WIN_PAD, 0, max(0, WIN_PAD - rounded_width), 0)
        controls_layout.activate()
        view.browsing_area.banners.setContentsMargins(
            WIN_PAD, 0, max(0, WIN_PAD - rounded_width), 0
        )
        self.update()

    def _finish_side_animation(self) -> None:
        view = self.layout()
        view.side_panel.setHidden(not self._is_side_open)
        view.side_panel.setMaximumWidth(self._no_max_width)
        view.content_splitter.setHandleWidth(self._content_handle_width)
        if self._is_side_open:
            side_panel_layout = unwrap(view.side_panel.layout())
            side_panel_layout.setEnabled(True)
            side_panel_layout.activate()

    def _place_side_panel_button(self) -> None:
        """Place the side panel button next to the search bar."""
        view = self.layout()
        central_widget = unwrap(self.centralWidget())
        search_bar_top = view.search_bar.layout().search_field.mapTo(central_widget, QPoint()).y()
        view.side_panel_button.move(
            central_widget.width() - _CLOSED_SEARCH_BAR_INSET, search_bar_top
        )

    def set_sorting_mode(self, mode: SortingModeEnum) -> None:
        self.layout().browsing_controls.set_sorting_mode(mode)

    def set_results_text(self, text: str) -> None:
        self.layout().browsing_controls.set_results_text(text)

    def set_pagination_actions_checked(self, is_infinite: bool, page_size: int) -> None:
        self.layout().browsing_controls.set_pagination_actions_checked(is_infinite, page_size)

    def set_show_filenames_action_checked(self, checked: bool) -> None:
        self.layout().browsing_controls.set_show_filenames_action_checked(checked)

    def _update_content_splitter_limit(self) -> None:
        """Update whether the side panel's handle is at a limit."""
        splitter = self.layout().content_splitter
        position = splitter.handle(1).x()
        lowest, highest = cast(tuple[int, int], splitter.getRange(1))
        set_at_limit(splitter, position <= lowest or position >= highest)

    def _corner_handle_content_widget(self) -> QWidget | None:
        if not self.inspector.is_preview_showing:
            return None
        return self.inspector.preview_widget

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            watched is self.layout().content_splitter.handle(1)
            and event.type() == QEvent.Type.MouseButtonPress
        ):
            self._update_content_splitter_limit()
        if (watched is self.centralWidget() and event.type() == QEvent.Type.Resize) or (
            watched is self.layout().search_bar.layout().search_field
            and event.type() == QEvent.Type.Move
        ):
            self._place_side_panel_button()
        # NOTE: When the grid is moved for the banner animation, the top edge doesn't get
        # repainted for some reason, so manually repaint it here.
        if watched is self.thumb_grid.scroll_area and event.type() in (
            QEvent.Type.Move,
            QEvent.Type.Resize,
        ):
            self._update_surface_top()
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
