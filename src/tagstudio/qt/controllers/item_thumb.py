# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path
from typing import TYPE_CHECKING, override

import structlog
from PySide6.QtCore import QEvent, QMimeData, QPoint, QRect, QRectF, QSignalBlocker, QSize, Qt, QUrl
from PySide6.QtGui import (
    QColor,
    QContextMenuEvent,
    QDrag,
    QEnterEvent,
    QGuiApplication,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from tagstudio.core.library.alchemy.enums import ItemType
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaTypes
from tagstudio.core.query_lang.file_groups import SEARCH
from tagstudio.core.utils.decompression import get_display_ext
from tagstudio.core.utils.str_formatting import format_duration
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.utils.file_opener import FileOpenerHelper
from tagstudio.qt.views.item_thumb_view import ItemThumbView
from tagstudio.qt.views.styles.palette import Palette
from tagstudio.qt.views.styles.stylesheets import (
    RADIUS,
    item_thumb_faded_select_color,
    item_thumb_filename_style,
    item_thumb_hover_color,
    item_thumb_label_style,
)

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.models import Entry
    from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)


class ItemThumb(QWidget):
    """The thumbnail widget for a library item (Entry, Entry Group, etc.)."""

    def __init__(
        self,
        mode: ItemType | None,
        library: Library,
        driver: QtDriver,
        thumb_size: tuple[int, int],
        show_filename_label: bool = False,
    ):
        super().__init__()
        self._driver = driver
        self._lib = library
        self._opener = FileOpenerHelper(Path())

        self._hover_color = item_thumb_hover_color()
        self._select_color = Palette.accent_alt()
        self._select_color_faded = item_thumb_faded_select_color()

        self._image_hovered: bool = False
        self._image: QPixmap | None = None
        self._item_path: Path | None = None
        self._mode: ItemType | None = mode
        self._press_pos: QPoint | None = None
        self._select_on_release: bool = False
        self._selected: bool = False
        self._show_filename_label: bool = show_filename_label
        self._thumb_size: tuple[int, int] = thumb_size
        self.item_id: int = -1
        self.rendered_path: Path | None = None

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(*thumb_size)
        self.setLayout(ItemThumbView(driver.entry_state.badge_tag_ids))
        self._connect_callbacks()
        self.set_filename_visibility(show_filename_label)
        self.set_mode(mode)

    @override
    def layout(self) -> ItemThumbView:
        return super().layout()  # pyright: ignore[reportReturnType]

    def _connect_callbacks(self) -> None:
        view = self.layout()
        view.open_file_action.triggered.connect(self._opener.open_file)
        view.open_explorer_action.triggered.connect(self._opener.open_explorer)
        view.delete_action.triggered.connect(self._on_delete)
        for tag_id, badge in view.badges.items():
            badge.stateChanged.connect(lambda _, t=tag_id: self._on_badge_check(t))

    def _on_delete(self) -> None:
        if self.item_id != -1 and self._item_path is not None:
            self._driver.delete_files_callback(self._item_path, self.item_id)

    def _toggle_item_selection(self) -> None:
        self._driver.toggle_item_selection(
            self.item_id,
            append=(QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier),
            bridge=(QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier),
        )

    def _image_rect(self) -> QRect:
        return QRect(0, 0, *self._thumb_size)

    def _set_image_hovered(self, hovered: bool) -> None:
        if hovered == self._image_hovered:
            return
        self._image_hovered = hovered
        self._show_check_badges(show=hovered)
        if hovered:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.unsetCursor()
        self.update()

    def set_mode(self, mode: ItemType | None) -> None:
        view = self.layout()
        if mode is None:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=True)
            self._set_image_hovered(hovered=False)
        elif mode == ItemType.ENTRY:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=False)
            view.badge_container.setHidden(False)
            # Count Label depends on file extension (video length, word count)
            view.item_type_icon.setHidden(True)
            view.count_label.setStyleSheet(item_thumb_label_style())
            view.count_label.setHidden(True)
            view.ext_label.setHidden(True)
        elif mode == ItemType.ENTRY_GROUP:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=False)
            view.badge_container.setHidden(True)
            view.ext_label.setHidden(True)
            view.count_label.setStyleSheet(item_thumb_label_style(is_large=True))
            view.count_label.setHidden(False)
            view.item_type_icon.setHidden(False)
        self._mode = mode
        self.update()

    def set_extension(self, filename: Path) -> None:
        show_ext_label = False
        show_count_label = False

        # TODO: Make these configurable by the user (on, off, or custom)
        ext = get_display_ext(filename)
        if ext and ext.startswith(".") is False:
            ext = "." + ext
        if (
            not MediaTypes.contains("image.raster", ext, SEARCH)
            or MediaTypes.contains("image.raster.raw", ext, SEARCH)
            or MediaTypes.contains("image.vector", ext, SEARCH)
            or MediaTypes.contains("adobe.photoshop", ext, SEARCH)
            or ext
            in [
                ".apng",
                ".avif",
                ".exr",
                ".gif",
                ".jxl",
                ".webp",
            ]
        ) and (ext or filename.stem):
            self.layout().ext_label.setText(ext.upper()[1:] or filename.stem.upper())
            show_ext_label = True

        if MediaTypes.contains("video", ext, SEARCH) or MediaTypes.contains("audio", ext, SEARCH):
            show_count_label = True

        self.layout().ext_label.setHidden(not show_ext_label)
        self.layout().count_label.setHidden(not show_count_label)

    def set_count(self, count: str) -> None:
        view = self.layout()
        if count:
            view.count_label.setHidden(False)
            view.count_label.setText(count)
        else:
            if self._mode == ItemType.ENTRY:
                view.ext_label.setHidden(True)
                view.count_label.setHidden(True)

    def set_duration(self, duration: float | None) -> None:
        """Show a media duration on the count label, or "-:--" while it's unknown."""
        count_label = self.layout().count_label
        if duration is None:
            count_label.setText("-:--")
        else:
            count_label.setText(format_duration(duration))
            count_label.setHidden(False)

    def set_filename_text(self, filename: Path):
        self.layout().file_label.setText(str(filename.name))

    def set_filename_visibility(self, set_visible: bool):
        """Toggle the visibility of the filename label.

        Args:
            set_visible (bool): Show the filename, true or false.
        """
        file_label = self.layout().file_label
        if set_visible:
            if file_label.isHidden():
                file_label.setHidden(False)
            self.setFixedHeight(
                self._thumb_size[1]
                + ItemThumbView.FILE_LABEL_HEIGHT
                + ItemThumbView.FILE_LABEL_SPACING
            )
        else:
            file_label.setHidden(True)
            self.setFixedHeight(self._thumb_size[1])
        self._show_filename_label = set_visible

    def set_selected(self, value: bool) -> None:
        if value != self._selected:
            self._selected = value
            self.layout().file_label.setStyleSheet(item_thumb_filename_style(is_selected=value))
            self.update()

    def set_thumb_size(self, size: int) -> None:
        self._thumb_size = (size, size)
        self._image = None
        self.setFixedSize(size, size)
        self.set_filename_visibility(self._show_filename_label)
        self.update()

    def set_image(self, image: QPixmap, size: QSize, file_path: Path) -> None:
        self._image = image
        self._thumb_size = size.width(), size.height()
        self.rendered_path = file_path
        self.update()

    def set_item(self, entry: Entry):
        self.set_item_id(entry.id)
        self._item_path = unwrap(self._lib.library_dir) / entry.path
        self._opener.set_filepath(self._item_path)

    def set_item_id(self, item_id: int):
        self.item_id = item_id

    def assign_badge(self, tag_id: int, value: bool) -> None:
        badge = self.layout().badges[tag_id]
        if badge.isChecked() != value:
            with QSignalBlocker(badge):
                badge.setChecked(value)
            badge.setHidden(not value)

    def _show_check_badges(self, show: bool):
        if self._mode != ItemType.TAG_GROUP:
            for badge in self.layout().badges.values():
                badge.setHidden(not (show or badge.isChecked()))

    def _on_badge_check(self, tag_id: int):
        selected = self._driver.selected
        entry_ids = selected if self.item_id in selected else [self.item_id]
        is_checked = self.layout().badges[tag_id].isChecked()
        self._driver.entry_state.set_tag(entry_ids, tag_id, is_checked)

    def _start_drag(self) -> None:
        drag = QDrag(self._driver)
        paths: list[QUrl] = []
        mimedata = QMimeData()

        selected_ids = self._driver.selected

        for entry_id in selected_ids:
            entry = self._lib.get_entry(entry_id)
            if not entry:
                continue

            url = QUrl.fromLocalFile(Path(unwrap(self._lib.library_dir)) / entry.path)
            paths.append(url)

        mimedata.setUrls(paths)
        drag.setMimeData(mimedata)
        drag.exec(Qt.DropAction.CopyAction)
        logger.info("[ItemThumb] Dragging Files:", entry_ids=selected_ids)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        if self._mode is None:
            return

        painter = QPainter(self)
        rect = self._image_rect()
        if self._image is not None:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawPixmap(rect, self._image)

        if self._image_hovered or self._selected:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            width = 3
            path = QPainterPath()
            path.addRoundedRect(
                QRectF(width / 2, width / 2, rect.width() - width, rect.height() - width),
                RADIUS,
                RADIUS,
            )

            if self._selected:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_HardLight)
                painter.setPen(QPen(self._select_color_faded, width))
                painter.fillPath(path, self._select_color_faded)
                painter.drawPath(path)

                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
                color: QColor = self._hover_color if self._image_hovered else self._select_color
                painter.setPen(QPen(color, width))
                painter.drawPath(path)
            else:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
                painter.setPen(QPen(self._hover_color, width))
                painter.drawPath(path)

        painter.end()

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self._set_image_hovered(self._image_rect().contains(event.position().toPoint()))
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self._set_image_hovered(hovered=False)
        return super().leaveEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if event.button() != Qt.MouseButton.LeftButton or not self._image_rect().contains(pos):
            return super().mousePressEvent(event)

        self._press_pos = pos
        ctrl = QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier
        self._select_on_release = False
        if ctrl or not self._selected:
            self._toggle_item_selection()
        elif len(self._driver.selected) > 1:
            # Wait for release so clicking a selected item can still drag the existing selection
            self._select_on_release = True

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._press_pos is None:
            return super().mouseReleaseEvent(event)

        self._press_pos = None
        if self._select_on_release and self._image_rect().contains(event.position().toPoint()):
            self._toggle_item_selection()

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        self._set_image_hovered(self._image_rect().contains(pos))
        if self._press_pos is None or event.buttons() != Qt.MouseButton.LeftButton:
            return
        if (pos - self._press_pos).manhattanLength() < QApplication.startDragDistance():
            return

        self._press_pos = None
        self._start_drag()

    @override
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if not self._image_rect().contains(event.pos()):
            return super().contextMenuEvent(event)

        view = self.layout()
        QMenu.exec(
            [view.open_file_action, view.open_explorer_action, view.delete_action],
            event.globalPos(),
            None,
            self,
        )
