# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import time
import typing
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING
from warnings import catch_warnings

import structlog
from PIL import Image, ImageQt
from PySide6.QtCore import QEvent, QMimeData, QSize, Qt, QUrl
from PySide6.QtGui import QAction, QDrag, QEnterEvent, QPixmap
from PySide6.QtWidgets import (
    QBoxLayout,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.library.alchemy.enums import ItemType
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaCategories, MediaType
from tagstudio.qt.flowlayout import FlowWidget
from tagstudio.qt.helpers.file_opener import FileOpenerHelper
from tagstudio.qt.platform_strings import open_file_str, trash_term
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.thumb_button import ThumbButton
from tagstudio.qt.widgets.thumb_renderer import ThumbRenderer

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class BadgeType(Enum):
    FAVORITE = "Favorite"
    ARCHIVED = "Archived"


BADGE_TAGS = {
    BadgeType.FAVORITE: TAG_FAVORITE,
    BadgeType.ARCHIVED: TAG_ARCHIVED,
}


def badge_update_lock(func):
    """Prevent recursively triggering badge updates."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.driver.badge_update_lock:
            return

        self.driver.badge_update_lock = True
        try:
            func(self, *args, **kwargs)
        except Exception:
            raise
        finally:
            self.driver.badge_update_lock = False

    return wrapper


class ItemThumb(FlowWidget):
    """The thumbnail widget for a library item (Entry, Collation, Tag Group, etc.)."""

    update_cutoff: float = time.time()

    collation_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[2] / "resources/qt/images/collation_icon_128.png")
    )
    collation_icon_128.load()

    tag_group_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[2] / "resources/qt/images/tag_group_icon_128.png")
    )
    tag_group_icon_128.load()

    small_text_style = (
        "background-color:rgba(0, 0, 0, 192);"
        "color:#FFFFFF;"
        "font-family:Oxanium;"
        "font-weight:bold;"
        "font-size:12px;"
        "border-radius:3px;"
        "padding-top: 4px;"
        "padding-right: 1px;"
        "padding-bottom: 1px;"
        "padding-left: 1px;"
    )

    med_text_style = (
        "background-color:rgba(0, 0, 0, 192);"
        "color:#FFFFFF;"
        "font-family:Oxanium;"
        "font-weight:bold;"
        "font-size:18px;"
        "border-radius:3px;"
        "padding-top: 4px;"
        "padding-right: 1px;"
        "padding-bottom: 1px;"
        "padding-left: 1px;"
    )

    filename_style = "font-size:10px;"

    def __init__(
        self,
        mode: ItemType | None,
        library: Library,
        driver: "QtDriver",
        thumb_size: tuple[int, int],
        show_filename_label: bool = False,
    ):
        super().__init__()
        self.lib = library
        self.mode: ItemType | None = mode
        self.driver = driver
        self.item_id: int | None = None
        self.thumb_size: tuple[int, int] = thumb_size
        self.show_filename_label: bool = show_filename_label
        self.label_height = 12
        self.label_spacing = 4
        self.setMinimumSize(*thumb_size)
        self.setMaximumSize(*thumb_size)
        self.setMouseTracking(True)
        check_size = 24
        self.setFixedSize(
            thumb_size[0],
            thumb_size[1]
            + ((self.label_height + self.label_spacing) if show_filename_label else 0),
        )

        self.thumb_container = QWidget()
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.setSpacing(0)
        self.setLayout(self.base_layout)

        # +----------+
        # |   ARC FAV| Top Right: Favorite & Archived Badges
        # |          |
        # |          |
        # |EXT      #| Lower Left: File Type, Tag Group Icon, or Collation Icon
        # +----------+ Lower Right: Collation Count, Video Length, or Word Count
        #
        #   Filename   Underneath: (Optional) Filename

        # Thumbnail ============================================================

        # +----------+
        # |*--------*|
        # ||        ||
        # ||        ||
        # |*--------*|
        # +----------+
        self.thumb_layout = QVBoxLayout(self.thumb_container)
        self.thumb_layout.setObjectName("baseLayout")
        self.thumb_layout.setContentsMargins(0, 0, 0, 0)

        # +----------+
        # |[~~~~~~~~]|
        # |          |
        # |          |
        # |          |
        # +----------+
        self.top_layout = QHBoxLayout()
        self.top_layout.setObjectName("topLayout")
        self.top_layout.setContentsMargins(6, 6, 6, 6)
        self.top_container = QWidget()
        self.top_container.setLayout(self.top_layout)
        self.thumb_layout.addWidget(self.top_container)

        # +----------+
        # |[~~~~~~~~]|
        # |     ^    |
        # |     |    |
        # |     v    |
        # +----------+
        self.thumb_layout.addStretch(2)

        # +----------+
        # |[~~~~~~~~]|
        # |     ^    |
        # |     v    |
        # |[~~~~~~~~]|
        # +----------+
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setObjectName("bottomLayout")
        self.bottom_layout.setContentsMargins(6, 6, 6, 6)
        self.bottom_container = QWidget()
        self.bottom_container.setLayout(self.bottom_layout)
        self.thumb_layout.addWidget(self.bottom_container)

        self.thumb_button = ThumbButton(self.thumb_container, thumb_size)
        self.renderer = ThumbRenderer(self.lib)
        self.renderer.updated.connect(
            lambda timestamp, image, size, filename: (
                self.update_thumb(timestamp, image=image),
                self.update_size(timestamp, size=size),
                self.set_filename_text(filename),
                self.set_extension(filename),
            )
        )
        self.thumb_button.setFlat(True)
        self.thumb_button.setLayout(self.thumb_layout)
        self.thumb_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        self.opener = FileOpenerHelper("")
        open_file_action = QAction(Translations["file.open_file"], self)
        open_file_action.triggered.connect(self.opener.open_file)
        open_explorer_action = QAction(open_file_str(), self)
        open_explorer_action.triggered.connect(self.opener.open_explorer)

        self.delete_action = QAction(
            Translations.format("trash.context.ambiguous", trash_term=trash_term()),
            self,
        )

        self.thumb_button.addAction(open_file_action)
        self.thumb_button.addAction(open_explorer_action)
        self.thumb_button.addAction(self.delete_action)

        # Static Badges ========================================================

        # Item Type Badge ------------------------------------------------------
        # Used for showing the Tag Group / Collation icons.
        # Mutually exclusive with the File Extension Badge.
        self.item_type_badge = QLabel()
        self.item_type_badge.setObjectName("itemBadge")
        self.item_type_badge.setPixmap(
            QPixmap.fromImage(
                ImageQt.ImageQt(
                    ItemThumb.collation_icon_128.resize(
                        (check_size, check_size), Image.Resampling.BILINEAR
                    )
                )
            )
        )
        self.item_type_badge.setMinimumSize(check_size, check_size)
        self.item_type_badge.setMaximumSize(check_size, check_size)
        self.bottom_layout.addWidget(self.item_type_badge)

        # File Extension Badge -------------------------------------------------
        # Mutually exclusive with the File Extension Badge.
        self.ext_badge = QLabel()
        self.ext_badge.setObjectName("extBadge")
        self.ext_badge.setStyleSheet(ItemThumb.small_text_style)
        self.bottom_layout.addWidget(self.ext_badge)
        self.bottom_layout.addStretch(2)

        # Count Badge ----------------------------------------------------------
        # Used for Tag Group + Collation counts, video length, word count, etc.
        self.count_badge = QLabel()
        self.count_badge.setObjectName("countBadge")
        self.count_badge.setText("-:--")
        self.count_badge.setStyleSheet(ItemThumb.small_text_style)
        self.bottom_layout.addWidget(self.count_badge, alignment=Qt.AlignmentFlag.AlignBottom)
        self.top_layout.addStretch(2)

        # Intractable Badges ===================================================
        self.cb_container = QWidget()
        self.cb_layout = QHBoxLayout()
        self.cb_layout.setDirection(QBoxLayout.Direction.RightToLeft)
        self.cb_layout.setContentsMargins(0, 0, 0, 0)
        self.cb_layout.setSpacing(6)
        self.cb_container.setLayout(self.cb_layout)
        self.top_layout.addWidget(self.cb_container)

        self.badge_active: dict[BadgeType, bool] = {
            BadgeType.FAVORITE: False,
            BadgeType.ARCHIVED: False,
        }

        self.badges: dict[BadgeType, QCheckBox] = {}
        badge_icons = {
            BadgeType.FAVORITE: (
                ":/images/star_icon_empty_128.png",
                ":/images/star_icon_filled_128.png",
            ),
            BadgeType.ARCHIVED: (
                ":/images/box_icon_empty_128.png",
                ":/images/box_icon_filled_128.png",
            ),
        }
        for badge_type in BadgeType:
            icon_empty, icon_checked = badge_icons[badge_type]
            badge = QCheckBox()
            badge.setObjectName(badge_type.name)
            badge.setToolTip(badge_type.value)
            badge.setStyleSheet(
                f"QCheckBox::indicator{{width: {check_size}px;height: {check_size}px;}}"
                f"QCheckBox::indicator::unchecked{{image: url({icon_empty})}}"
                f"QCheckBox::indicator::checked{{image: url({icon_checked})}}"
            )
            badge.setMinimumSize(check_size, check_size)
            badge.setMaximumSize(check_size, check_size)
            badge.setHidden(True)

            badge.stateChanged.connect(lambda x, bt=badge_type: self.on_badge_check(bt))

            self.badges[badge_type] = badge
            self.cb_layout.addWidget(badge)

        # Filename Label =======================================================
        self.file_label = QLabel(Translations["generic.filename"])
        self.file_label.setStyleSheet(ItemThumb.filename_style)
        self.file_label.setMaximumHeight(self.label_height)
        if not show_filename_label:
            self.file_label.setHidden(True)

        self.base_layout.addWidget(self.thumb_container)
        self.base_layout.addWidget(self.file_label)

        self.set_mode(mode)

    @property
    def is_favorite(self) -> bool:
        return self.badge_active[BadgeType.FAVORITE]

    @property
    def is_archived(self) -> bool:
        return self.badge_active[BadgeType.ARCHIVED]

    def set_mode(self, mode: ItemType | None) -> None:
        if mode is None:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=True)
            self.thumb_button.unsetCursor()
            self.thumb_button.setHidden(True)
        elif mode == ItemType.ENTRY and self.mode != ItemType.ENTRY:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=False)
            self.thumb_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.thumb_button.setHidden(False)
            self.cb_container.setHidden(False)
            # Count Badge depends on file extension (video length, word count)
            self.item_type_badge.setHidden(True)
            self.count_badge.setStyleSheet(ItemThumb.small_text_style)
            self.count_badge.setHidden(True)
            self.ext_badge.setHidden(True)
        elif mode == ItemType.COLLATION and self.mode != ItemType.COLLATION:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=False)
            self.thumb_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.thumb_button.setHidden(False)
            self.cb_container.setHidden(True)
            self.ext_badge.setHidden(True)
            self.count_badge.setStyleSheet(ItemThumb.med_text_style)
            self.count_badge.setHidden(False)
            self.item_type_badge.setHidden(False)
        elif mode == ItemType.TAG_GROUP and self.mode != ItemType.TAG_GROUP:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=False)
            self.thumb_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.thumb_button.setHidden(False)
            self.ext_badge.setHidden(True)
            self.count_badge.setHidden(False)
            self.item_type_badge.setHidden(False)
        self.mode = mode

    def set_extension(self, filename: Path) -> None:
        ext = filename.suffix
        if ext and ext.startswith(".") is False:
            ext = "." + ext
        media_types: set[MediaType] = MediaCategories.get_types(ext)
        if (
            not MediaCategories.is_ext_in_category(ext, MediaCategories.IMAGE_TYPES)
            or MediaCategories.is_ext_in_category(ext, MediaCategories.IMAGE_RAW_TYPES)
            or MediaCategories.is_ext_in_category(ext, MediaCategories.IMAGE_VECTOR_TYPES)
            or MediaCategories.is_ext_in_category(ext, MediaCategories.ADOBE_PHOTOSHOP_TYPES)
            or ext
            in [
                ".apng",
                ".avif",
                ".exr",
                ".gif",
                ".jxl",
                ".webp",
            ]
        ):
            self.ext_badge.setHidden(False)
            self.ext_badge.setText(ext.upper()[1:] or filename.stem.upper())
            if MediaType.VIDEO in media_types or MediaType.AUDIO in media_types:
                self.count_badge.setHidden(False)
        else:
            if self.mode == ItemType.ENTRY:
                self.ext_badge.setHidden(True)
                self.count_badge.setHidden(True)

    def set_count(self, count: str) -> None:
        if count:
            self.count_badge.setHidden(False)
            self.count_badge.setText(count)
        else:
            if self.mode == ItemType.ENTRY:
                self.ext_badge.setHidden(True)
                self.count_badge.setHidden(True)

    def set_filename_text(self, filename: Path | None):
        self.set_item_path(filename)
        self.file_label.setText(str(filename.name))

    def set_filename_visibility(self, set_visible: bool):
        """Toggle the visibility of the filename label.

        Args:
            set_visible (bool): Show the filename, true or false.
        """
        if set_visible:
            if self.file_label.isHidden():
                self.file_label.setHidden(False)
            self.setFixedHeight(self.thumb_size[1] + self.label_height + self.label_spacing)
        else:
            self.file_label.setHidden(True)
            self.setFixedHeight(self.thumb_size[1])
        self.show_filename_label = set_visible

    def update_thumb(self, timestamp: float, image: QPixmap | None = None):
        """Update attributes of a thumbnail element."""
        if timestamp > ItemThumb.update_cutoff:
            self.thumb_button.setIcon(image if image else QPixmap())

    def update_size(self, timestamp: float, size: QSize):
        """Updates attributes of a thumbnail element.

        Args:
            timestamp (float | None): The UTC timestamp for when this call was
                originally dispatched. Used to skip outdated jobs.

            size (QSize): The new thumbnail size to set.
        """
        if timestamp > ItemThumb.update_cutoff:
            self.thumb_size = size.toTuple()  # type: ignore
            self.thumb_button.setIconSize(size)
            self.thumb_button.setMinimumSize(size)
            self.thumb_button.setMaximumSize(size)

    def update_clickable(self, clickable: typing.Callable):
        """Updates attributes of a thumbnail element."""
        if clickable:
            with catch_warnings(record=True):
                self.thumb_button.clicked.disconnect()
            self.thumb_button.clicked.connect(clickable)

    def set_item_id(self, item_id: int):
        self.item_id = item_id

    def set_item_path(self, path: Path | str | None):
        """Set the absolute filepath for the item. Used for locating on disk."""
        self.opener.set_filepath(path)

    def assign_badge(self, badge_type: BadgeType, value: bool) -> None:
        mode = self.mode
        # blank mode to avoid recursive badge updates
        self.mode = None
        badge = self.badges[badge_type]
        self.badge_active[badge_type] = value
        if badge.isChecked() != value:
            badge.setChecked(value)
            badge.setHidden(not value)

        self.mode = mode

    def show_check_badges(self, show: bool):
        if self.mode != ItemType.TAG_GROUP:
            for badge_type, badge in self.badges.items():
                is_hidden = not (show or self.badge_active[badge_type])
                badge.setHidden(is_hidden)

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        self.show_check_badges(show=True)
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802
        self.show_check_badges(show=False)
        return super().leaveEvent(event)

    @badge_update_lock
    def on_badge_check(self, badge_type: BadgeType):
        if self.mode is None:
            return

        toggle_value = self.badges[badge_type].isChecked()
        self.badge_active[badge_type] = toggle_value
        badge_values: dict[BadgeType, bool] = {badge_type: toggle_value}
        self.driver.update_badges(badge_values, self.item_id)

    def toggle_item_tag(
        self,
        entry_id: int,
        toggle_value: bool,
        tag_id: int,
    ):
        if entry_id in self.driver.selected and self.driver.main_window.preview_panel.is_open:
            if len(self.driver.selected) == 1:
                self.driver.main_window.preview_panel.fields.update_toggled_tag(
                    tag_id, toggle_value
                )
            else:
                pass

    def mouseMoveEvent(self, event):  # noqa: N802
        if event.buttons() is not Qt.MouseButton.LeftButton:
            return

        drag = QDrag(self.driver)
        paths: list[QUrl] = []
        mimedata = QMimeData()

        selected_ids = self.driver.selected

        for entry_id in selected_ids:
            entry = self.lib.get_entry(entry_id)
            if not entry:
                continue

            url = QUrl.fromLocalFile(Path(self.lib.library_dir) / entry.path)
            paths.append(url)

        mimedata.setUrls(paths)
        drag.setMimeData(mimedata)
        drag.exec(Qt.DropAction.CopyAction)
        logger.info("[ItemThumb] Dragging Files:", entry_ids=selected_ids)
