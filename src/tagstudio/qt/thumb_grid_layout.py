import math
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLayout, QLayoutItem, QScrollArea

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.library.alchemy.enums import ItemType
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.qt.widgets.item_thumb import BadgeType, ItemThumb
from tagstudio.qt.widgets.thumb_renderer import ThumbRenderer

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class ThumbGridLayout(QLayout):
    def __init__(self, driver: "QtDriver", scroll_area: QScrollArea) -> None:
        super().__init__(None)
        self.driver: QtDriver = driver
        self.scroll_area: QScrollArea = scroll_area

        self._item_thumbs: list[ItemThumb] = []
        self._items: list[QLayoutItem] = []
        # Entry.id -> _entry_ids[index]
        self._selected: dict[int, int] = {}
        # _entry_ids[index]
        self._last_selected: int | None = None

        self._entry_ids: list[int] = []
        self._entries: dict[int, Entry] = {}
        # Tag.id -> {Entry.id}
        self._tag_entries: dict[int, set[int]] = {}
        self._entry_paths: dict[Path, int] = {}
        # Entry.id -> _items[index]
        self._entry_items: dict[int, int] = {}

        self._render_results: dict[Path, Any] = {}
        self._renderer: ThumbRenderer = ThumbRenderer(self.driver.lib)
        self._renderer.updated.connect(self._on_rendered)
        self._render_cutoff: float = 0.0

        # _entry_ids[StartIndex:EndIndex]
        self._last_page_update: tuple[int, int] | None = None

    def set_entries(self, entry_ids: list[int]):
        self.scroll_area.verticalScrollBar().setValue(0)

        self._selected.clear()
        self._last_selected = None

        self._entry_ids = entry_ids
        self._entries.clear()
        self._tag_entries.clear()
        self._entry_paths.clear()

        self._entry_items.clear()
        self._render_results.clear()
        self.driver.thumb_job_queue.queue.clear()
        self._render_cutoff = time.time()

        base_size: tuple[int, int] = (
            self.driver.main_window.thumb_size,
            self.driver.main_window.thumb_size,
        )
        self.driver.thumb_job_queue.put(
            (
                self._renderer.render,
                (
                    self._render_cutoff,
                    Path(),
                    base_size,
                    self.driver.main_window.devicePixelRatio(),
                    True,
                    True,
                ),
            )
        )

        self._last_page_update = None

    def select_all(self):
        self._selected.clear()
        for index, id in enumerate(self._entry_ids):
            self._selected[id] = index
            self._last_selected = index

        for entry_id in self._entry_items:
            self._set_selected(entry_id)

    def select_inverse(self):
        selected = {}
        for index, id in enumerate(self._entry_ids):
            if id not in self._selected:
                selected[id] = index
                self._last_selected = index

        for id in self._selected:
            if id not in selected:
                self._set_selected(id, value=False)
        for id in selected:
            self._set_selected(id)

        self._selected = selected

    def select_entry(self, entry_id: int):
        if entry_id in self._selected:
            index = self._selected.pop(entry_id)
            if index == self._last_selected:
                self._last_selected = None
            self._set_selected(entry_id, value=False)
        else:
            try:
                index = self._entry_ids.index(entry_id)
            except ValueError:
                index = -1

            self._selected[entry_id] = index
            self._last_selected = index
            self._set_selected(entry_id)

    def select_to_entry(self, entry_id: int):
        index = self._entry_ids.index(entry_id)
        if len(self._selected) == 0:
            self.select_entry(entry_id)
            return
        if self._last_selected is None:
            # TODO
            self._last_selected = min(self._selected.values(), key=lambda i: abs(index - i))

        start = self._last_selected
        self._last_selected = index

        if start > index:
            index, start = start, index
        else:
            index += 1

        for i in range(start, index):
            entry_id = self._entry_ids[i]
            self._selected[entry_id] = i
            self._set_selected(entry_id)

    def clear_selected(self):
        for entry_id in self._entry_items:
            self._set_selected(entry_id, value=False)

        self._selected.clear()
        self._last_selected = None

    def _set_selected(self, entry_id: int, value: bool = True):
        if entry_id not in self._entry_items:
            return
        index = self._entry_items[entry_id]
        if index < len(self._item_thumbs):
            self._item_thumbs[index].thumb_button.set_selected(value)

    def add_tags(self, entry_ids: list[int], tag_ids: list[int]):
        for tag_id in tag_ids:
            self._tag_entries.setdefault(tag_id, set()).update(entry_ids)

    def remove_tags(self, entry_ids: list[int], tag_ids: list[int]):
        for tag_id in tag_ids:
            self._tag_entries.setdefault(tag_id, set()).difference_update(entry_ids)

    def _fetch_entries(self, ids: list[int]):
        entries = self.driver.lib.get_entries(ids)
        for entry in entries:
            self._entry_paths[self.driver.lib.library_dir / entry.path] = entry.id
            self._entries[entry.id] = entry

        tag_ids = [TAG_ARCHIVED, TAG_FAVORITE]
        tag_entries = self.driver.lib.get_tag_entries(tag_ids, ids)
        for tag_id in tag_ids:
            if tag_id not in self._tag_entries:
                self._tag_entries[tag_id] = tag_entries[tag_id]
                continue
            new = tag_entries[tag_id]
            current = self._tag_entries[tag_id]
            for id in ids:
                if id in new:
                    current.add(id)
                elif id in current:
                    current.remove(id)

    def _on_rendered(self, timestamp: float, image: QPixmap, size: QSize, file_path: Path):
        if timestamp < self._render_cutoff:
            return
        self._render_results[file_path] = (timestamp, image, size, file_path)

        # If this is the loading image update all item_thumbs with pending thumbnails
        if file_path == Path():
            for path, entry_id in self._entry_paths.items():
                if self._render_results.get(path, None) is None:
                    self._update_thumb(entry_id, image, size, file_path)
            return

        if file_path not in self._entry_paths:
            return
        entry_id = self._entry_paths[file_path]
        self._update_thumb(entry_id, image, size, file_path)

    def _update_thumb(self, entry_id: int, image: QPixmap, size: QSize, file_path: Path):
        index = self._entry_items.get(entry_id)
        if index is None:
            return
        item_thumb = self._item_thumbs[index]
        item_thumb.update_thumb(image)
        item_thumb.update_size(size)
        item_thumb.set_filename_text(file_path)
        item_thumb.set_extension(file_path)

    def _item_thumb(self, index: int) -> ItemThumb:
        if w := getattr(self.driver, "main_window", None):
            base_size = (w.thumb_size, w.thumb_size)
        else:
            base_size = (128, 128)
        while index >= len(self._item_thumbs):
            item = ItemThumb(
                ItemType.ENTRY, self.driver.lib, self.driver, base_size, show_filename_label=True
            )
            item.set_filename_visibility(self.driver.settings.show_filenames_in_grid)
            self._item_thumbs.append(item)
            self.addWidget(item)
        return self._item_thumbs[index]

    def _size(self, width: int) -> tuple[int, int, int]:
        if len(self._entry_ids) == 0:
            return 0, 0, 0
        spacing = self.spacing()

        _item_thumb = self._item_thumb(0)
        item = self._items[0]
        item_size = item.sizeHint()
        item_width = item_size.width()
        item_height = item_size.height()

        width_offset = item_width + spacing
        height_offset = item_height + spacing

        if width_offset == 0:
            return 0, 0, height_offset
        per_row = int(width / width_offset)

        return per_row, width_offset, height_offset

    @override
    def heightForWidth(self, arg__1: int) -> int:
        width = arg__1
        per_row, _, height_offset = self._size(width)
        if per_row == 0:
            return height_offset
        return math.ceil(len(self._entry_ids) / per_row) * height_offset

    @override
    def setGeometry(self, arg__1: QRect) -> None:
        super().setGeometry(arg__1)
        rect = arg__1
        if len(self._entry_ids) == 0:
            for item in self._item_thumbs:
                item.setGeometry(32_000, 32_000, 0, 0)
            return

        per_row, width_offset, height_offset = self._size(rect.right())
        view_height = self.parentWidget().parentWidget().height()
        offset = self.scroll_area.verticalScrollBar().value()
        top_row_hidden = (offset % height_offset) / height_offset

        visible_rows = math.ceil((view_height + (offset % height_offset)) / height_offset)
        offset = int(offset / height_offset)
        start = offset * per_row
        end = start + (visible_rows * per_row)

        # Load closest off screen row
        # Loads both top and bottom if equally close
        if top_row_hidden <= 0.5:
            start -= per_row * 3
        if top_row_hidden >= 0.5 or top_row_hidden == 0.0:
            end += per_row * 3

        start = max(0, start)
        end = min(len(self._entry_ids), end)
        if (start, end) == self._last_page_update:
            return
        self._last_page_update = (start, end)

        # Clear render queue if len > 2 pages
        if len(self.driver.thumb_job_queue.queue) > (per_row * visible_rows * 2):
            self.driver.thumb_job_queue.queue.clear()
            pending = []
            for k, v in self._render_results.items():
                if v is None and k != Path():
                    pending.append(k)
            for k in pending:
                self._render_results.pop(k)

        # Reorder items so previously rendered rows will reuse same item_thumbs
        # When scrolling down top row gets moved to end of list
        _ = self._item_thumb(end - start - 1)
        for item_index, i in enumerate(range(start, end)):
            if i >= len(self._entry_ids):
                continue
            entry_id = self._entry_ids[i]
            if entry_id not in self._entry_items:
                continue
            prev_item_index = self._entry_items[entry_id]
            if item_index == prev_item_index:
                break
            diff = prev_item_index - item_index
            self._items = self._items[diff:] + self._items[:diff]
            self._item_thumbs = self._item_thumbs[diff:] + self._item_thumbs[:diff]
            break
        self._entry_items.clear()

        # Move unused item_thumbs off screen
        count = end - start
        for item in self._item_thumbs[count:]:
            item.setGeometry(32_000, 32_000, 0, 0)

        ratio = self.driver.main_window.devicePixelRatio()
        base_size: tuple[int, int] = (
            self.driver.main_window.thumb_size,
            self.driver.main_window.thumb_size,
        )
        timestamp = time.time()
        for item_index, i in enumerate(range(start, end)):
            if i >= len(self._entry_ids):
                continue
            entry_id = self._entry_ids[i]
            if entry_id not in self._entries:
                ids = [id for id in self._entry_ids[start:end] if id not in self._entries]
                self._fetch_entries(ids)

            entry = self._entries[entry_id]
            row = int(i / per_row)
            self._entry_items[entry_id] = item_index
            item_thumb = self._item_thumb(item_index)
            item = self._items[item_index]
            col = i % per_row
            item_x = width_offset * col
            item_y = height_offset * row
            item_thumb.setGeometry(QRect(QPoint(item_x, item_y), item.sizeHint()))
            file_path = self.driver.lib.library_dir / entry.path
            item_thumb.set_item(entry)

            if result := self._render_results.get(file_path):
                _t, im, s, p = result
                if item_thumb.rendered_path == p:
                    continue
                self._update_thumb(entry_id, im, s, p)
            else:
                if Path() in self._render_results:
                    _t, im, s, p = self._render_results[Path()]
                    self._update_thumb(entry_id, im, s, p)

                if file_path not in self._render_results:
                    self._render_results[file_path] = None
                    self.driver.thumb_job_queue.put(
                        (
                            self._renderer.render,
                            (timestamp, file_path, base_size, ratio, False, True),
                        )
                    )

        # set_selected causes stutters making thumbs after selected not show for a frame
        # setting it after positioning thumbs fixes this
        for i in range(start, end):
            if i >= len(self._entry_ids):
                continue
            entry_id = self._entry_ids[i]
            item_index = self._entry_items[entry_id]
            item_thumb = self._item_thumbs[item_index]
            item_thumb.thumb_button.set_selected(entry_id in self._selected)

            item_thumb.assign_badge(BadgeType.ARCHIVED, entry_id in self._tag_entries[TAG_ARCHIVED])
            item_thumb.assign_badge(BadgeType.FAVORITE, entry_id in self._tag_entries[TAG_FAVORITE])

    @override
    def addItem(self, arg__1: QLayoutItem) -> None:
        self._items.append(arg__1)

    @override
    def count(self) -> int:
        return len(self._entries)

    @override
    def hasHeightForWidth(self) -> bool:
        return True

    @override
    def itemAt(self, index: int) -> QLayoutItem:
        if index >= len(self._items):
            return None
        return self._items[index]

    @override
    def sizeHint(self) -> QSize:
        self._item_thumb(0)
        return self._items[0].minimumSize()
