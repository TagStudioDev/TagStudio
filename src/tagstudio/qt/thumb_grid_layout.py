import math
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLayout, QLayoutItem, QScrollArea

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.library.alchemy.enums import ItemType
from tagstudio.core.library.alchemy.library import GroupedSearchResult
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.group_header import GroupHeaderWidget
from tagstudio.qt.mixed.item_thumb import BadgeType, ItemThumb
from tagstudio.qt.previews.renderer import ThumbRenderer

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

        # Grouping support
        self._grouped_result: GroupedSearchResult | None = None
        self._group_headers: list[GroupHeaderWidget] = []
        self._group_dividers: list[QFrame] = []
        # Flat list of ("header", group_idx), ("divider", divider_idx), or ("thumb", entry_id)
        self._layout_items: list[tuple[str, int]] = []
        # Track total height for grouped layout
        self._grouped_total_height: int = 0

        self._render_results: dict[Path, Any] = {}
        self._renderer: ThumbRenderer = ThumbRenderer(self.driver)
        self._renderer.updated.connect(self._on_rendered)
        self._render_cutoff: float = 0.0

        # _entry_ids[StartIndex:EndIndex]
        self._last_page_update: tuple[int, int] | None = None

    def set_entries(self, entry_ids: list[int], grouped_result: GroupedSearchResult | None = None):
        self.scroll_area.verticalScrollBar().setValue(0)

        self._selected.clear()
        self._last_selected = None

        self._entry_ids = entry_ids
        self._grouped_result = grouped_result
        self._entries.clear()
        self._tag_entries.clear()
        self._entry_paths.clear()

        if grouped_result:
            self._build_grouped_layout()
        else:
            for header in self._group_headers:
                header.deleteLater()
            for divider in self._group_dividers:
                divider.deleteLater()
            self._group_headers = []
            self._group_dividers = []
            self._layout_items = []
            self._grouped_total_height = 0

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

    def _build_grouped_layout(self):
        """Build flat list of layout items for grouped rendering."""
        if not self._grouped_result:
            self._layout_items = []
            return

        self._layout_items = []

        old_collapsed_states = {}
        if self._group_headers:
            for idx, header in enumerate(self._group_headers):
                old_collapsed_states[idx] = header.is_collapsed
            for header in self._group_headers:
                header.deleteLater()
            for divider in self._group_dividers:
                divider.deleteLater()
            self._group_headers = []
            self._group_dividers = []

        for group_idx, group in enumerate(self._grouped_result.groups):
            if group_idx > 0:
                from PySide6.QtWidgets import QWidget
                divider = QWidget()
                divider.setStyleSheet("QWidget { background-color: #444444; }")
                divider.setFixedHeight(1)
                divider.setMinimumWidth(1)
                self._group_dividers.append(divider)
                self.addWidget(divider)
                self._layout_items.append(("divider", len(self._group_dividers) - 1))

            self._layout_items.append(("header", group_idx))

            default_collapsed = group.is_special and group.special_label == "No Tag"
            is_collapsed = old_collapsed_states.get(group_idx, default_collapsed)
            header = GroupHeaderWidget(
                tag=group.tag,
                entry_count=len(group.entry_ids),
                is_collapsed=is_collapsed,
                is_special=group.is_special,
                special_label=group.special_label,
                library=self.driver.lib,
                is_first=group_idx == 0,
                tags=group.tags,
            )
            header.toggle_collapsed.connect(
                lambda g_idx=group_idx: self._on_group_collapsed(g_idx)
            )
            self._group_headers.append(header)
            self.addWidget(header)

            if not is_collapsed:
                for entry_id in group.entry_ids:
                    self._layout_items.append(("thumb", entry_id))

    def _on_group_collapsed(self, group_idx: int):
        """Handle group header collapse/expand."""
        if not self._grouped_result or group_idx >= len(self._group_headers):
            return

        self._build_grouped_layout()

        self._last_page_update = None
        current_geometry = self.geometry()
        self.setGeometry(current_geometry)

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
        ids = [id for id in ids if id not in self._entries]
        entries = self.driver.lib.get_entries(ids)
        for entry in entries:
            self._entry_paths[unwrap(self.driver.lib.library_dir) / entry.path] = entry.id
            self._entries[entry.id] = entry

        tag_ids = [TAG_ARCHIVED, TAG_FAVORITE]
        tag_entries = self.driver.lib.get_tag_entries(tag_ids, ids)
        for tag_id, entries in tag_entries.items():
            self._tag_entries.setdefault(tag_id, set()).update(entries)

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
        item_thumb.update_thumb(image, file_path)
        item_thumb.update_size(size)
        item_thumb.set_filename_text(file_path)
        item_thumb.set_extension(file_path)

    def _item_thumb(self, index: int) -> ItemThumb:
        if w := getattr(self.driver, "main_window", None):
            base_size = (w.thumb_size, w.thumb_size)
        else:
            base_size = (128, 128)
        while index >= len(self._item_thumbs):
            show_filename = self.driver.settings.show_filenames_in_grid
            item = ItemThumb(
                ItemType.ENTRY,
                self.driver.lib,
                self.driver,
                base_size,
                show_filename_label=show_filename,
            )
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

        # Use calculated grouped height if in grouped mode
        if self._grouped_result is not None and self._grouped_total_height > 0:
            return self._grouped_total_height

        return math.ceil(len(self._entry_ids) / per_row) * height_offset

    @override
    def setGeometry(self, arg__1: QRect) -> None:
        super().setGeometry(arg__1)
        rect = arg__1
        if len(self._entry_ids) == 0:
            for item in self._item_thumbs:
                item.setGeometry(32_000, 32_000, 0, 0)
            for header in self._group_headers:
                header.setGeometry(32_000, 32_000, 0, 0)
            return

        # Use grouped rendering if layout items exist
        if self._layout_items:
            self._setGeometry_grouped(rect)
            return

        per_row, width_offset, height_offset = self._size(rect.right())
        view_height = self.parentWidget().parentWidget().height()
        offset = self.scroll_area.verticalScrollBar().value()

        visible_rows = math.ceil((view_height + (offset % height_offset)) / height_offset)
        offset = int(offset / height_offset)
        start = offset * per_row
        end = start + (visible_rows * per_row)

        # Load closest off screen rows
        start -= per_row * 3
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
            entry_id = self._entry_ids[i]
            if entry_id not in self._entries:
                ids = self._entry_ids[start:end]
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
            file_path = unwrap(self.driver.lib.library_dir) / entry.path
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

    def _setGeometry_grouped(self, rect: QRect):  # noqa: N802
        """Render layout in grouped mode with headers and thumbnails."""
        header_height = 32
        per_row, width_offset, height_offset = self._size(rect.right())

        for item in self._item_thumbs:
            item.setGeometry(32_000, 32_000, 0, 0)
        for header in self._group_headers:
            header.setGeometry(32_000, 32_000, 0, 0)
        for divider in self._group_dividers:
            divider.setGeometry(32_000, 32_000, 0, 0)

        current_y = 0
        current_group_row = 0
        thumb_in_current_row = 0
        thumbs_in_current_group = 0
        item_thumb_index = 0
        self._entry_items.clear()

        ratio = self.driver.main_window.devicePixelRatio()
        base_size: tuple[int, int] = (
            self.driver.main_window.thumb_size,
            self.driver.main_window.thumb_size,
        )
        timestamp = time.time()

        for item_type, item_id in self._layout_items:
            if item_type == "divider":
                if thumbs_in_current_group > 0:
                    rows_needed = math.ceil(thumbs_in_current_group / per_row)
                    current_y += rows_needed * height_offset

                current_y += 8
                if item_id < len(self._group_dividers):
                    divider = self._group_dividers[item_id]
                    divider.setGeometry(QRect(0, current_y, rect.width(), 1))
                current_y += 1
                current_y += 8

                current_group_row = 0
                thumb_in_current_row = 0
                thumbs_in_current_group = 0

            elif item_type == "header":
                if thumbs_in_current_group > 0:
                    rows_needed = math.ceil(thumbs_in_current_group / per_row)
                    current_y += rows_needed * height_offset

                if item_id < len(self._group_headers):
                    header = self._group_headers[item_id]
                    header.setGeometry(QRect(0, current_y, rect.width(), header_height))
                current_y += header_height

                current_group_row = 0
                thumb_in_current_row = 0
                thumbs_in_current_group = 0

            elif item_type == "thumb":
                entry_id = item_id
                if entry_id not in self._entries:
                    self._fetch_entries([entry_id])

                if entry_id not in self._entries:
                    continue

                entry = self._entries[entry_id]

                if item_thumb_index >= len(self._item_thumbs):
                    item_thumb = self._item_thumb(item_thumb_index)
                else:
                    item_thumb = self._item_thumbs[item_thumb_index]

                self._entry_items[entry_id] = item_thumb_index

                col = thumb_in_current_row % per_row
                item_x = width_offset * col
                item_y = current_y + (current_group_row * height_offset)

                size_hint = self._items[min(item_thumb_index, len(self._items) - 1)].sizeHint()
                item_thumb.setGeometry(QRect(QPoint(item_x, item_y), size_hint))
                item_thumb.set_item(entry)

                file_path = unwrap(self.driver.lib.library_dir) / entry.path
                if result := self._render_results.get(file_path):
                    _t, im, s, p = result
                    if item_thumb.rendered_path != p:
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

                item_thumb.thumb_button.set_selected(entry_id in self._selected)
                item_thumb.assign_badge(
                    BadgeType.ARCHIVED, entry_id in self._tag_entries.get(TAG_ARCHIVED, set())
                )
                item_thumb.assign_badge(
                    BadgeType.FAVORITE, entry_id in self._tag_entries.get(TAG_FAVORITE, set())
                )

                item_thumb_index += 1
                thumb_in_current_row += 1
                thumbs_in_current_group += 1

                if thumb_in_current_row % per_row == 0:
                    current_group_row += 1

        if thumbs_in_current_group > 0:
            rows_needed = math.ceil(thumbs_in_current_group / per_row)
            current_y += rows_needed * height_offset

        self._grouped_total_height = current_y

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
    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    @override
    def sizeHint(self) -> QSize:
        self._item_thumb(0)
        return self._items[0].minimumSize()
