# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import time
from pathlib import Path
from typing import TYPE_CHECKING, override

import structlog
from PySide6.QtCore import QEvent, QObject, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import QScrollArea, QWidget

from tagstudio.core.library.alchemy.enums import ItemType
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.types import unwrap
from tagstudio.previews.media_probe import can_have_duration, get_duration
from tagstudio.qt.controllers.item_thumb import ItemThumb
from tagstudio.qt.qt_file_renderer import QtFileRenderer
from tagstudio.qt.views.layouts.thumb_grid_layout import ThumbGridLayout

if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)


class ThumbGrid(QWidget):
    """A scrollable grid of item thumbnails."""

    DURATION_DELAY_MS = 200  # Allows fast scrolling without getting lagged by duration labels
    RESIZE_RENDER_DELAY_MS = 200  # Allows more responsive rapid resizing
    SHOW_THUMBS_DELAY_MS = 200  # Allows quick renders to appear together without a loading flash

    _duration_loaded = Signal(Path, object)
    _entries_fetched = Signal(int, object, object)
    visible_changed = Signal(int)  # ID of the first visible entry

    def __init__(self, driver: QtDriver, scroll_area: QScrollArea) -> None:
        super().__init__()
        self.setObjectName("thumb_grid")
        self._driver = driver
        self._renderer = QtFileRenderer(driver.lib, driver.settings)

        self._duration_timer = QTimer(self)
        self._duration_timer.setInterval(self.DURATION_DELAY_MS)
        self._duration_timer.setSingleShot(True)
        self._resize_render_timer = QTimer(self)
        self._resize_render_timer.setInterval(self.RESIZE_RENDER_DELAY_MS)
        self._resize_render_timer.setSingleShot(True)
        self._show_thumbs_timer = QTimer(self)
        self._show_thumbs_timer.setInterval(self.SHOW_THUMBS_DELAY_MS)
        self._show_thumbs_timer.setSingleShot(True)

        self._changed_while_fetching: set[int] = set()
        self._durations: dict[Path, float | None] = {}
        self._entries: dict[int, Entry] = {}
        self._entry_ids: list[int] = []
        self._entry_indices: dict[int, int] = {}
        self._entry_paths: dict[Path, int] = {}
        self._fetch_pool: QThreadPool | None = None
        self._fetching: set[int] = set()
        self._generation = 0
        self._held: set[ItemThumb] = set()
        self._last_entries_time = 0.0
        self._loading_image: QPixmap | None = None
        self._pending_durations: set[Path] = set()
        self._previous_size_renders: dict[Path, QPixmap] = {}
        self._render_cutoff = 0.0
        self._renders: dict[Path, QPixmap | None] = {}
        self._scroll_to: int | None = None

        self.setLayout(ThumbGridLayout(scroll_area, self._create_thumb))
        self._connect_callbacks(scroll_area)

    @override
    def layout(self) -> ThumbGridLayout[ItemThumb]:
        return super().layout()  # pyright: ignore[reportReturnType]

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Clear selected entries when clicking the background
        if (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
            and isinstance(self.childAt(event.position().toPoint()), ItemThumb | None)
            and self._driver.selection.selected
        ):
            self._driver.selection.clear()
        super().mousePressEvent(event)

    def _connect_callbacks(self, scroll_area: QScrollArea) -> None:
        scroll_area.installEventFilter(self)
        scroll_area.verticalScrollBar().valueChanged.connect(lambda _: self.layout().update())
        self.layout().items_assigned.connect(self._on_items_assigned)
        self.layout().items_unassigned.connect(self._on_items_unassigned)
        self.layout().first_visible_changed.connect(
            lambda index: self.visible_changed.emit(self._entry_ids[index])
        )
        self._renderer.updated.connect(self._on_rendered)
        self._resize_render_timer.timeout.connect(self._request_renders)
        self._show_thumbs_timer.timeout.connect(self._show_held_entries)
        self._duration_timer.timeout.connect(self._queue_durations)
        self._entries_fetched.connect(self._on_entries_fetched)
        self._duration_loaded.connect(self._on_duration_loaded)
        self._driver.entry_state.tags_changed.connect(self._on_tags_changed)
        self._driver.selection.changed.connect(self._update_selected)

    def set_entries(self, entry_ids: list[int]) -> None:
        self._generation += 1
        self._resize_render_timer.stop()
        self._entry_ids = entry_ids
        self._entry_indices = {entry_id: index for index, entry_id in enumerate(entry_ids)}
        self._entries.clear()
        self._entry_paths.clear()
        self._fetching.clear()
        self._changed_while_fetching.clear()
        self._driver.entry_state.unload_badges()
        self._previous_size_renders.clear()
        self._reset_renders()
        if self._fetch_pool is not None:
            self._fetch_pool.clear()
        now = time.monotonic()
        if now - self._last_entries_time < self.SHOW_THUMBS_DELAY_MS / 1000:
            # Show entries immediately if the results are changing quickly.
            # Traversing pages or searching quickly feels much more responsive.
            self._show_thumbs_timer.stop()
        else:
            # Use the delay to wait and show ready thumbnails all at once.
            # Prevents a weird "popcorn"/"waterfall" effect and overall looks much nicer.
            self._show_thumbs_timer.start()
        self._last_entries_time = now
        self.layout().set_item_count(len(entry_ids))

        index = None if self._scroll_to is None else self._entry_indices.get(self._scroll_to)
        self._scroll_to = None
        self.layout().scroll_to_index(index or 0)

    def scroll_to(self, entry_id: int) -> None:
        """Scroll to this entry once the next entries are set."""
        self._scroll_to = entry_id

    def set_thumb_size(self, size: int) -> None:
        self._previous_size_renders.update(
            (path, image) for path, image in self._renders.items() if image is not None
        )
        self._reset_renders()
        self._show_loading_images()
        self._resize_render_timer.start()
        first_visible = self.layout().first_visible_index()
        for thumb in self.layout().widgets():
            thumb.set_thumb_size(size)
        if first_visible is not None:
            self.layout().scroll_to_index(first_visible)
        self.layout().activate()

    def set_filenames_visible(self, visible: bool) -> None:
        for thumb in self.layout().widgets():
            thumb.set_filename_visibility(visible)
        self.layout().activate()

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            # NOTE: macOS marks arrow keys as keypad keys:
            # https://doc.qt.io/qt-6/qt.html#KeyboardModifier-enum
            modifiers = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
            is_shift = modifiers == Qt.KeyboardModifier.ShiftModifier
            if (is_shift or modifiers == Qt.KeyboardModifier.NoModifier) and self._move_selection(
                Qt.Key(event.key()), extend=is_shift
            ):
                return True
        return super().eventFilter(watched, event)

    def _move_selection(self, key: Qt.Key, extend: bool) -> bool:
        """Move or extend the selection with an arrow key.

        Returns:
            bool: True if `key` is an arrow key.
        """
        if key not in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            return False
        if not self._entry_ids:
            return True

        # Paginated results are treated as a single result set that's visually broken up, meaning:
        # - Arrow keys move to adjacent pages for navigation and selection
        # - Arrow keys will jump to the page with the navigated entry
        results = self._driver.frame_content
        page_start = self._driver.browsing_history.current.page_index * self._driver.page_size
        cursor = self._driver.selection.cursor
        if cursor in results:
            target = self._index_in_direction(results.index(cursor), key)
        else:
            target = page_start + (self.layout().first_visible_index() or 0)
        target = self._driver.selection.move_selection(results, target, extend)

        page = target // self._driver.page_size
        if page != self._driver.browsing_history.current.page_index:
            self.scroll_to(results[target])
            self._driver.page_move(page, absolute=True)
        else:
            pagination = self._driver.main_window.pagination
            bottom_padding = pagination.height() if pagination.isVisible() else 0
            self.layout().ensure_visible(target - page_start, bottom_padding)
        return True

    def _index_in_direction(self, index: int, key: Qt.Key) -> int:
        """The index of the next item from `index` in an arrow key's direction, across all pages."""
        per_row = self.layout().items_per_row()
        page_size = self._driver.page_size
        last = len(self._driver.frame_content) - 1
        page_start = index - index % page_size
        page_end = min(page_start + page_size - 1, last)
        column = (index - page_start) % per_row
        match key:
            case Qt.Key.Key_Left:
                return max(index - 1, 0)
            case Qt.Key.Key_Right:
                return min(index + 1, last)
            case Qt.Key.Key_Up:
                if index - per_row >= page_start:
                    return index - per_row
                if page_start == 0:
                    return index
                # The same (or closest) column in the PREVIOUS page's last row
                previous_start = page_start - page_size
                last_row_start = previous_start + (page_size - 1) // per_row * per_row
                return min(last_row_start + column, page_start - 1)
            case _:
                last_row_start = page_start + (page_end - page_start) // per_row * per_row
                # The same (or closest) column in THIS page's next row
                if index < last_row_start:
                    return min(index + per_row, page_end)
                if page_end == last:
                    return index
                # The same (or closest) column in the NEXT page's first row
                return min(page_end + 1 + column, page_end + page_size, last)

    def _update_selected(self) -> None:
        for _, thumb in self.layout().assigned_items():
            if thumb not in self._held:
                thumb.set_selected(self._driver.selection.is_selected(thumb.item_id))

    def _create_thumb(self) -> ItemThumb:
        size = self._driver.main_window.thumb_size
        return ItemThumb(
            ItemType.ENTRY,
            self._driver.lib,
            self._driver,
            (size, size),
            show_filename_label=self._driver.settings.show_filenames_in_grid,
        )

    def _path(self, entry: Entry) -> Path:
        return unwrap(self._driver.lib.library_dir) / entry.path

    def _thumb_for(self, entry_id: int | None) -> ItemThumb | None:
        index = None if entry_id is None else self._entry_indices.get(entry_id)
        return None if index is None else self.layout().widget_at(index)

    def _on_items_assigned(self, items: list[tuple[int, ItemThumb]]) -> None:
        missing: list[int] = []
        for index, thumb in items:
            entry_id = self._entry_ids[index]
            thumb.set_item_id(entry_id)
            if entry_id not in self._entries and entry_id not in self._fetching:
                missing.append(entry_id)
            if self._show_thumbs_timer.isActive() and thumb.rendered_path is not None:
                self._held.add(thumb)
            else:
                self._show_entry(thumb)

        if missing:
            self._fetch_entries(missing)
        self._trim_render_queue()
        self._request_renders()

    def _show_entry(self, thumb: ItemThumb) -> None:
        """Show a thumbnail's entry or placeholders while the entry is fetched."""
        self._held.discard(thumb)
        entry = self._entries.get(thumb.item_id)
        if entry is None:
            self._clear_thumb(thumb)
            self._show_loading_image(thumb)
        else:
            self._assign_entry(thumb, entry)
        thumb.set_selected(self._driver.selection.is_selected(thumb.item_id))

    def _clear_thumb(self, thumb: ItemThumb) -> None:
        """Remove the entry details and image a thumbnail is showing."""
        thumb.set_selected(False)
        thumb.set_filename_text(Path())
        thumb.set_extension(Path())
        for tag_id in self._driver.entry_state.badge_tag_ids:
            thumb.assign_badge(tag_id, value=False)
        thumb.clear_image()

    def _show_held_entries(self) -> None:
        self._show_thumbs_timer.stop()
        for thumb in list(self._held):
            self._show_entry(thumb)

    def _held_renders_ready(self) -> bool:
        """Whether every held thumbnail on screen has its render."""
        for thumb in self._held:
            entry = self._entries.get(thumb.item_id)
            if thumb.visibleRegion().isEmpty():
                continue
            if entry is None or self._renders.get(self._path(entry)) is None:
                return False
        return True

    def _assign_entry(self, thumb: ItemThumb, entry: Entry) -> None:
        path = self._path(entry)
        thumb.set_item(entry)
        thumb.set_filename_text(path)
        thumb.set_extension(path)
        thumb.set_duration(self._durations.get(path))
        self._assign_badges(thumb, entry.id)

        image = self._renders.get(path) or self._previous_size_renders.get(path)
        if image is not None:
            thumb.set_image(image, path)
        elif thumb.rendered_path != path:
            self._show_loading_image(thumb)

    def _on_items_unassigned(self, thumbs: list[ItemThumb]) -> None:
        for thumb in thumbs:
            self._held.discard(thumb)
            thumb.clear_image()

    def _show_loading_image(self, thumb: ItemThumb) -> None:
        thumb.set_image(unwrap(self._loading_image), Path())

    def _assign_badges(self, thumb: ItemThumb, entry_id: int) -> None:
        for tag_id in self._driver.entry_state.badge_tag_ids:
            thumb.assign_badge(tag_id, self._driver.entry_state.has_badge(entry_id, tag_id))

    def _on_tags_changed(self, entry_ids: set[int]) -> None:
        self._changed_while_fetching.update(self._fetching.intersection(entry_ids))
        for _, thumb in self.layout().assigned_items():
            if (
                thumb.item_id in entry_ids
                and thumb.item_id in self._entries
                and thumb not in self._held
            ):
                self._assign_badges(thumb, thumb.item_id)

    def _fetch_entries(self, entry_ids: list[int]) -> None:
        """Read entries and their badge tags on a worker thread."""
        self._fetching.update(entry_ids)
        lib = self._driver.lib
        generation = self._generation
        badge_tag_ids = self._driver.entry_state.badge_tag_ids

        def fetch() -> None:
            try:
                entries = lib.get_entries(entry_ids)
                tag_entries = lib.get_tag_entries(badge_tag_ids, entry_ids)
            except Exception as e:
                logger.error("[ThumbGrid] Error fetching entries", error=e)
                return
            self._entries_fetched.emit(generation, entries, tag_entries)

        if self._fetch_pool is None:
            self._fetch_pool = QThreadPool(self)
            self._fetch_pool.setMaxThreadCount(1)
        self._fetch_pool.start(fetch)

    def _on_entries_fetched(
        self, generation: int, entries: list[Entry], tag_entries: dict[int, set[int]]
    ) -> None:
        if generation != self._generation:
            return

        entry_ids = [entry.id for entry in entries]
        self._fetching.difference_update(entry_ids)
        fresh = [e for e in entry_ids if e not in self._changed_while_fetching]
        self._changed_while_fetching.difference_update(entry_ids)
        self._driver.entry_state.cache_badges(fresh, tag_entries)
        for entry in entries:
            self._entries[entry.id] = entry
            self._entry_paths[self._path(entry)] = entry.id
            if (thumb := self._thumb_for(entry.id)) is not None and thumb not in self._held:
                self._assign_entry(thumb, entry)
        self._request_renders()

    def _reset_renders(self) -> None:
        self._render_cutoff = time.time()
        self._renders.clear()
        size = self._driver.main_window.thumb_size
        self._loading_image = self._renderer.loading_image((size, size), self.devicePixelRatio())
        self._driver.thumb_job_queue.queue.clear()
        self._pending_durations.clear()

    def _show_loading_images(self) -> None:
        """Show the loading image on assigned thumbnails that don't have their render yet."""
        for _, thumb in self.layout().assigned_items():
            entry = self._entries.get(thumb.item_id)
            if entry is None or thumb.rendered_path != self._path(entry):
                self._show_loading_image(thumb)

    def _request_renders(self) -> None:
        """Queue renders for thumbnails, starting at the first visible one."""
        if self._resize_render_timer.isActive():
            return

        size = self._driver.main_window.thumb_size
        ratio = self._driver.main_window.devicePixelRatio()
        timestamp = time.time()
        for entry in self._assigned_entries():
            path = self._path(entry)
            if path in self._renders:
                continue
            self._renders[path] = None
            self._driver.thumb_job_queue.put(
                (
                    self._renderer.render,
                    (
                        self._driver.cache_manager,
                        timestamp,
                        path,
                        (size, size),
                        ratio,
                        False,
                        True,
                        entry.date_modified,
                    ),
                )
            )
        self._duration_timer.start()

    def _assigned_entries(self) -> list[Entry]:
        """Entries of the assigned thumbnails, starting at the first visible one."""
        first_visible = self.layout().first_visible_index() or 0
        assigned = sorted(self.layout().assigned_items(), key=lambda item: item[0] < first_visible)
        return [entry for _, thumb in assigned if (entry := self._entries.get(thumb.item_id))]

    def _trim_render_queue(self) -> None:
        """Trim queued renders once they get too backed up."""
        queue = self._driver.thumb_job_queue.queue
        if len(queue) <= 2 * len(self.layout().assigned_items()):
            return

        queue.clear()
        self._pending_durations.clear()
        self._renders = {path: image for path, image in self._renders.items() if image is not None}

    def _on_rendered(
        self, timestamp: float, image: QPixmap, file_path: Path, _border_color: QColor | None
    ) -> None:
        if timestamp < self._render_cutoff:
            return

        self._renders[file_path] = image
        self._previous_size_renders.pop(file_path, None)
        thumb = self._thumb_for(self._entry_paths.get(file_path))
        if thumb in self._held:
            if self._held_renders_ready():
                self._show_held_entries()
        elif thumb is not None:
            thumb.set_image(image, file_path)

    def _queue_durations(self) -> None:
        for entry in self._assigned_entries():
            path = self._path(entry)
            if (
                not can_have_duration(path)
                or path in self._durations
                or path in self._pending_durations
            ):
                continue
            self._pending_durations.add(path)
            self._driver.thumb_job_queue.put((self._load_duration, (path,)))

    def _load_duration(self, file_path: Path) -> None:
        self._duration_loaded.emit(file_path, get_duration(file_path))

    def _on_duration_loaded(self, file_path: Path, duration: float | None) -> None:
        self._pending_durations.discard(file_path)
        self._durations[file_path] = duration
        thumb = self._thumb_for(self._entry_paths.get(file_path))
        if thumb is not None and thumb not in self._held:
            thumb.set_duration(duration)
