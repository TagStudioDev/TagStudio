# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import time
from pathlib import Path
from typing import TYPE_CHECKING, override

import structlog
from PySide6.QtCore import QSize, QThreadPool, QTimer, Signal
from PySide6.QtGui import QPixmap
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

    RESIZE_RENDER_DELAY_MS = 200  # Allows for more responsive rapid resizing

    visible_changed = Signal(int)  # ID of the first visible entry
    _entries_fetched = Signal(int, object, object)
    _duration_loaded = Signal(Path, object)

    def __init__(self, driver: QtDriver, scroll_area: QScrollArea) -> None:
        super().__init__()
        self.setObjectName("thumb_grid")
        self._driver = driver
        self._renderer = QtFileRenderer(driver.lib, driver.settings)

        self._durations: dict[Path, float | None] = {}
        self._entries: dict[int, Entry] = {}
        self._entry_ids: list[int] = []
        self._entry_indices: dict[int, int] = {}
        self._entry_paths: dict[Path, int] = {}
        self._fetch_pool: QThreadPool | None = None
        self._fetching: set[int] = set()
        self._changed_while_fetching: set[int] = set()
        self._generation = 0
        self._loading_image: QPixmap | None = None
        self._pending_durations: set[Path] = set()
        self._previous_size_renders: dict[Path, QPixmap] = {}
        self._render_cutoff = 0.0
        self._renders: dict[Path, QPixmap | None] = {}
        self._resize_render_timer = QTimer(self)
        self._resize_render_timer.setInterval(self.RESIZE_RENDER_DELAY_MS)
        self._resize_render_timer.setSingleShot(True)
        self._scroll_to: int | None = None

        self.setLayout(ThumbGridLayout(scroll_area, self._create_thumb))
        self._connect_callbacks(scroll_area)

    @override
    def layout(self) -> ThumbGridLayout[ItemThumb]:
        return super().layout()  # pyright: ignore[reportReturnType]

    def _connect_callbacks(self, scroll_area: QScrollArea) -> None:
        scroll_area.verticalScrollBar().valueChanged.connect(lambda _: self.layout().update())
        self.layout().items_bound.connect(self._on_items_bound)
        self.layout().first_visible_changed.connect(
            lambda index: self.visible_changed.emit(self._entry_ids[index])
        )
        self._renderer.updated.connect(self._on_rendered)
        self._resize_render_timer.timeout.connect(self._request_renders)
        self._entries_fetched.connect(self._on_entries_fetched)
        self._duration_loaded.connect(self._on_duration_loaded)
        self._driver.entry_state.tags_changed.connect(self._on_tags_changed)

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

    def update_selected(self) -> None:
        for _, thumb in self.layout().bound_items():
            thumb.set_selected(thumb.item_id in self._driver._selected)  # pyright: ignore[reportPrivateUsage]

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

    def _thumb_for(self, entry_id: int) -> ItemThumb | None:
        index = self._entry_indices.get(entry_id)
        return None if index is None else self.layout().widget_at(index)

    def _on_items_bound(self, items: list[tuple[int, ItemThumb]]) -> None:
        missing: list[int] = []
        for index, thumb in items:
            entry_id = self._entry_ids[index]
            thumb.set_item_id(entry_id)
            thumb.set_selected(entry_id in self._driver._selected)  # pyright: ignore[reportPrivateUsage]
            entry = self._entries.get(entry_id)
            if entry is not None:
                self._bind_entry(thumb, entry)
                continue

            thumb.set_filename_text(Path())
            thumb.set_extension(Path())
            for tag_id in self._driver.entry_state.badge_tag_ids:
                thumb.assign_badge(tag_id, value=False)
            self._show_loading_image(thumb)
            if entry_id not in self._fetching:
                missing.append(entry_id)

        if missing:
            self._fetch_entries(missing)
        self._trim_render_queue()
        self._request_renders()

    def _bind_entry(self, thumb: ItemThumb, entry: Entry) -> None:
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

    def _show_loading_image(self, thumb: ItemThumb) -> None:
        if self._loading_image is None:
            thumb.clear_image()
        else:
            thumb.set_image(self._loading_image, Path())

    def _assign_badges(self, thumb: ItemThumb, entry_id: int) -> None:
        for tag_id in self._driver.entry_state.badge_tag_ids:
            thumb.assign_badge(tag_id, self._driver.entry_state.has_badge(entry_id, tag_id))

    def _on_tags_changed(self, entry_ids: set[int]) -> None:
        self._changed_while_fetching.update(self._fetching.intersection(entry_ids))
        for _, thumb in self.layout().bound_items():
            if thumb.item_id in entry_ids and thumb.item_id in self._entries:
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
            if (thumb := self._thumb_for(entry.id)) is not None:
                self._bind_entry(thumb, entry)
        self._request_renders()

    def _reset_renders(self) -> None:
        self._render_cutoff = time.time()
        self._renders.clear()
        self._loading_image = None
        self._driver.thumb_job_queue.queue.clear()
        self._pending_durations.clear()
        self._request_loading_image()

    def _request_loading_image(self) -> None:
        size = self._driver.main_window.thumb_size
        self._driver.thumb_job_queue.put(
            (
                self._renderer.render,
                (
                    self._driver.cache_manager,
                    self._render_cutoff,
                    Path(),
                    (size, size),
                    self._driver.main_window.devicePixelRatio(),
                    True,
                    True,
                ),
            )
        )

    def _request_renders(self) -> None:
        """Queue renders for thumbnails, starting at the first visible one."""
        if self._resize_render_timer.isActive():
            return

        first_visible = self.layout().first_visible_index() or 0
        bound = sorted(self.layout().bound_items(), key=lambda item: item[0] < first_visible)
        entries = [entry for _, thumb in bound if (entry := self._entries.get(thumb.item_id))]
        size = self._driver.main_window.thumb_size
        ratio = self._driver.main_window.devicePixelRatio()
        timestamp = time.time()
        for entry in entries:
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

        # Queued after thumbnails so they don't hold up rendering
        for entry in entries:
            self._queue_duration(self._path(entry))

    def _trim_render_queue(self) -> None:
        """Trim queued renders once they get too backed up."""
        queue = self._driver.thumb_job_queue.queue
        if len(queue) <= 2 * len(self.layout().bound_items()):
            return

        queue.clear()
        self._pending_durations.clear()
        self._renders = {path: image for path, image in self._renders.items() if image is not None}
        if self._loading_image is None:
            self._request_loading_image()

    def _on_rendered(self, timestamp: float, image: QPixmap, _size: QSize, file_path: Path) -> None:
        if timestamp < self._render_cutoff:
            return

        if file_path == Path():
            self._loading_image = image
            for _, thumb in self.layout().bound_items():
                entry = self._entries.get(thumb.item_id)
                if entry is None or thumb.rendered_path != self._path(entry):
                    thumb.set_image(image, Path())
            return

        self._renders[file_path] = image
        self._previous_size_renders.pop(file_path, None)
        entry_id = self._entry_paths.get(file_path)
        thumb = None if entry_id is None else self._thumb_for(entry_id)
        if thumb is not None:
            thumb.set_image(image, file_path)

    def _queue_duration(self, file_path: Path) -> None:
        if (
            not can_have_duration(file_path)
            or file_path in self._durations
            or file_path in self._pending_durations
        ):
            return
        self._pending_durations.add(file_path)
        self._driver.thumb_job_queue.put((self._load_duration, (file_path,)))

    def _load_duration(self, file_path: Path) -> None:
        self._duration_loaded.emit(file_path, get_duration(file_path))

    def _on_duration_loaded(self, file_path: Path, duration: float | None) -> None:
        self._pending_durations.discard(file_path)
        self._durations[file_path] = duration
        entry_id = self._entry_paths.get(file_path)
        thumb = None if entry_id is None else self._thumb_for(entry_id)
        if thumb is not None:
            thumb.set_duration(duration)
