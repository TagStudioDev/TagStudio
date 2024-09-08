# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio
import time
import typing
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from PIL import Image, ImageQt
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtGui import QPixmap, QEnterEvent, QAction
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QBoxLayout,
    QCheckBox,
)

from src.core.constants import (
    AUDIO_TYPES,
    VIDEO_TYPES,
    IMAGE_TYPES,
    TAG_FAVORITE,
    TAG_ARCHIVED,
)
from src.core.library import ItemType, Entry, Library
from src.core.library.alchemy.enums import FilterState
from src.core.library.alchemy.fields import _FieldID

from src.qt.flowlayout import FlowWidget
from src.qt.helpers.file_opener import FileOpenerHelper
from src.qt.widgets.thumb_renderer import ThumbRenderer
from src.qt.widgets.thumb_button import ThumbButton

if TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

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
    """
    The thumbnail widget for a library item (Entry, Collation, Tag Group, etc.).
    """

    update_cutoff: float = time.time()

    collation_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[3] / "resources/qt/images/collation_icon_128.png")
    )
    collation_icon_128.load()

    tag_group_icon_128: Image.Image = Image.open(
        str(Path(__file__).parents[3] / "resources/qt/images/tag_group_icon_128.png")
    )
    tag_group_icon_128.load()

    small_text_style = (
        f"background-color:rgba(0, 0, 0, 192);"
        f"font-family:Oxanium;"
        f"font-weight:bold;"
        f"font-size:12px;"
        f"border-radius:3px;"
        f"padding-top: 4px;"
        f"padding-right: 1px;"
        f"padding-bottom: 1px;"
        f"padding-left: 1px;"
    )

    med_text_style = (
        f"background-color:rgba(0, 0, 0, 192);"
        f"font-family:Oxanium;"
        f"font-weight:bold;"
        f"font-size:18px;"
        f"border-radius:3px;"
        f"padding-top: 4px;"
        f"padding-right: 1px;"
        f"padding-bottom: 1px;"
        f"padding-left: 1px;"
    )

    def __init__(
        self,
        mode: ItemType,
        library: Library,
        driver: "QtDriver",
        thumb_size: tuple[int, int],
        grid_idx: int,
    ):
        super().__init__()
        self.grid_idx = grid_idx
        self.lib = library
        self.mode: ItemType = mode
        self.driver = driver
        self.item_id: int | None = None
        self.thumb_size: tuple[int, int] = thumb_size
        self.setMinimumSize(*thumb_size)
        self.setMaximumSize(*thumb_size)
        check_size = 24
        # self.setStyleSheet('background-color:red;')

        # +----------+
        # |   ARC FAV| Top Right: Favorite & Archived Badges
        # |          |
        # |          |
        # |EXT      #| Lower Left: File Type, Tag Group Icon, or Collation Icon
        # +----------+ Lower Right: Collation Count, Video Length, or Word Count

        # Thumbnail ============================================================

        # +----------+
        # |*--------*|
        # ||        ||
        # ||        ||
        # |*--------*|
        # +----------+
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        # self.base_layout.setRowStretch(1, 2)
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        # +----------+
        # |[~~~~~~~~]|
        # |          |
        # |          |
        # |          |
        # +----------+
        self.top_layout = QHBoxLayout()
        self.top_layout.setObjectName("topLayout")
        # self.top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # self.top_layout.setColumnStretch(1, 2)
        self.top_layout.setContentsMargins(6, 6, 6, 6)
        self.top_container = QWidget()
        self.top_container.setLayout(self.top_layout)
        self.base_layout.addWidget(self.top_container)

        # +----------+
        # |[~~~~~~~~]|
        # |     ^    |
        # |     |    |
        # |     v    |
        # +----------+
        self.base_layout.addStretch(2)

        # +----------+
        # |[~~~~~~~~]|
        # |     ^    |
        # |     v    |
        # |[~~~~~~~~]|
        # +----------+
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setObjectName("bottomLayout")
        # self.bottom_container.setAlignment(Qt.AlignmentFlag.AlignBottom)
        # self.bottom_layout.setColumnStretch(1, 2)
        self.bottom_layout.setContentsMargins(6, 6, 6, 6)
        self.bottom_container = QWidget()
        self.bottom_container.setLayout(self.bottom_layout)
        self.base_layout.addWidget(self.bottom_container)

        # self.root_layout = QGridLayout(self)
        # self.root_layout.setObjectName('rootLayout')
        # self.root_layout.setColumnStretch(1, 2)
        # self.root_layout.setRowStretch(1, 2)
        # self.root_layout.setContentsMargins(6,6,6,6)
        # # root_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.thumb_button = ThumbButton(self, thumb_size)
        self.renderer = ThumbRenderer()
        self.renderer.updated.connect(
            lambda ts, i, s, ext: (
                self.update_thumb(ts, image=i),
                self.update_size(ts, size=s),
                self.set_extension(ext),
            )
        )
        self.thumb_button.setFlat(True)

        # self.bg_button.setStyleSheet('background-color:blue;')
        # self.bg_button.setLayout(self.root_layout)
        self.thumb_button.setLayout(self.base_layout)
        # self.bg_button.setMinimumSize(*thumb_size)
        # self.bg_button.setMaximumSize(*thumb_size)

        self.thumb_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.opener = FileOpenerHelper("")
        open_file_action = QAction("Open file", self)
        open_file_action.triggered.connect(self.opener.open_file)
        open_explorer_action = QAction("Open file in explorer", self)
        open_explorer_action.triggered.connect(self.opener.open_explorer)
        self.thumb_button.addAction(open_file_action)
        self.thumb_button.addAction(open_explorer_action)

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
        # self.root_layout.addWidget(self.item_type_badge, 2, 0)
        self.bottom_layout.addWidget(self.item_type_badge)

        # File Extension Badge -------------------------------------------------
        # Mutually exclusive with the File Extension Badge.
        self.ext_badge = QLabel()
        self.ext_badge.setObjectName("extBadge")
        # self.ext_badge.setText('MP4')
        # self.ext_badge.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.ext_badge.setStyleSheet(ItemThumb.small_text_style)
        # self.type_badge.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.root_layout.addWidget(self.ext_badge, 2, 0)
        self.bottom_layout.addWidget(self.ext_badge)
        # self.type_badge.setHidden(True)
        # bl_layout.addWidget(self.type_badge)

        self.bottom_layout.addStretch(2)

        # Count Badge ----------------------------------------------------------
        # Used for Tag Group + Collation counts, video length, word count, etc.
        self.count_badge = QLabel()
        self.count_badge.setObjectName("countBadge")
        # self.count_badge.setMaximumHeight(17)
        self.count_badge.setText("-:--")
        # self.count_badge.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.count_badge.setStyleSheet(ItemThumb.small_text_style)
        # self.count_badge.setAlignment(Qt.AlignmentFlag.AlignBottom)
        # self.root_layout.addWidget(self.count_badge, 2, 2)
        self.bottom_layout.addWidget(
            self.count_badge, alignment=Qt.AlignmentFlag.AlignBottom
        )

        self.top_layout.addStretch(2)

        # Intractable Badges ===================================================
        self.cb_container = QWidget()
        # check_badges.setStyleSheet('background-color:cyan;')
        self.cb_layout = QHBoxLayout()
        self.cb_layout.setDirection(QBoxLayout.Direction.RightToLeft)
        self.cb_layout.setContentsMargins(0, 0, 0, 0)
        self.cb_layout.setSpacing(6)
        self.cb_container.setLayout(self.cb_layout)
        # self.cb_container.setHidden(True)
        # self.root_layout.addWidget(self.check_badges, 0, 2)
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

        self.set_mode(mode)

    @property
    def is_favorite(self) -> bool:
        return self.badge_active[BadgeType.FAVORITE]

    @property
    def is_archived(self):
        return self.badge_active[BadgeType.ARCHIVED]

    def set_mode(self, mode: ItemType | None) -> None:
        if mode is None:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.unsetCursor()
            self.thumb_button.setHidden(True)
            # self.check_badges.setHidden(True)
            # self.ext_badge.setHidden(True)
            # self.item_type_badge.setHidden(True)
        elif mode == ItemType.ENTRY and self.mode != ItemType.ENTRY:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.thumb_button.setHidden(False)
            self.cb_container.setHidden(False)
            # Count Badge depends on file extension (video length, word count)
            self.item_type_badge.setHidden(True)
            self.count_badge.setStyleSheet(ItemThumb.small_text_style)
            self.count_badge.setHidden(True)
            self.ext_badge.setHidden(True)
        elif mode == ItemType.COLLATION and self.mode != ItemType.COLLATION:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.thumb_button.setHidden(False)
            self.cb_container.setHidden(True)
            self.ext_badge.setHidden(True)
            self.count_badge.setStyleSheet(ItemThumb.med_text_style)
            self.count_badge.setHidden(False)
            self.item_type_badge.setHidden(False)
        elif mode == ItemType.TAG_GROUP and self.mode != ItemType.TAG_GROUP:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.thumb_button.setHidden(False)
            # self.cb_container.setHidden(True)
            self.ext_badge.setHidden(True)
            self.count_badge.setHidden(False)
            self.item_type_badge.setHidden(False)
        self.mode = mode
        # logging.info(f'Set Mode To: {self.mode}')

    def set_extension(self, ext: str) -> None:
        if ext and ext.startswith(".") is False:
            ext = "." + ext
        if ext and ext not in IMAGE_TYPES or ext in [".gif", ".apng"]:
            self.ext_badge.setHidden(False)
            self.ext_badge.setText(ext.upper()[1:])
            if ext in VIDEO_TYPES + AUDIO_TYPES:
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

    def update_thumb(self, timestamp: float, image: QPixmap | None = None):
        """Update attributes of a thumbnail element."""
        # logging.info(f'[GUI] Updating Thumbnail for element {id(element)}: {id(image) if image else None}')
        if timestamp > ItemThumb.update_cutoff:
            self.thumb_button.setIcon(image if image else QPixmap())
            # element.repaint()

    def update_size(self, timestamp: float, size: QSize):
        """Updates attributes of a thumbnail element."""
        # logging.info(f'[GUI] Updating size for element {id(element)}:  {size.__str__()}')
        if timestamp > ItemThumb.update_cutoff and self.thumb_button.iconSize != size:
            self.thumb_button.setIconSize(size)
            self.thumb_button.setMinimumSize(size)
            self.thumb_button.setMaximumSize(size)

    def update_clickable(self, clickable: typing.Callable):
        """Updates attributes of a thumbnail element."""
        # logging.info(f'[GUI] Updating Click Event for element {id(element)}: {id(clickable) if clickable else None}')
        if self.thumb_button.is_connected:
            self.thumb_button.clicked.disconnect()
        if clickable:
            self.thumb_button.clicked.connect(clickable)
            self.thumb_button.is_connected = True

    def refresh_badge(self, entry: Entry | None = None):
        if not entry:
            if not self.item_id:
                logger.error("missing both entry and item_id")
                return None

            entry = self.lib.get_entry(self.item_id)
            if not entry:
                logger.error("Entry not found", item_id=self.item_id)
                return

        self.assign_badge(BadgeType.ARCHIVED, entry.is_archived)
        self.assign_badge(BadgeType.FAVORITE, entry.is_favorited)

    def set_item_id(self, entry: Entry):
        filepath = self.lib.library_dir / entry.path
        self.opener.set_filepath(filepath)
        self.item_id = entry.id

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

    def enterEvent(self, event: QEnterEvent) -> None:
        self.show_check_badges(True)
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.show_check_badges(False)
        return super().leaveEvent(event)

    @badge_update_lock
    def on_badge_check(self, badge_type: BadgeType):
        if self.mode is None:
            return

        toggle_value = self.badges[badge_type].isChecked()

        self.badge_active[badge_type] = toggle_value
        tag_id = BADGE_TAGS[badge_type]

        # check if current item is selected. if so, update all selected items
        if self.grid_idx in self.driver.selected:
            update_items = self.driver.selected
        else:
            update_items = [self.grid_idx]

        for idx in update_items:
            entry = self.driver.frame_content[idx]
            self.toggle_item_tag(
                entry, toggle_value, tag_id, _FieldID.TAGS_META.name, True
            )
            # update the entry
            self.driver.frame_content[idx] = self.lib.search_library(
                FilterState(id=entry.id)
            )[1][0]

        self.driver.update_badges(update_items)

    def toggle_item_tag(
        self,
        entry: Entry,
        toggle_value: bool,
        tag_id: int,
        field_key: str,
        create_field: bool = False,
    ):
        logger.info(
            "toggle_item_tag",
            entry_id=entry.id,
            toggle_value=toggle_value,
            tag_id=tag_id,
            field_key=field_key,
        )

        tag = self.lib.get_tag(tag_id)
        if toggle_value:
            self.lib.add_field_tag(entry, tag, field_key, create_field)
        else:
            self.lib.remove_field_tag(entry, tag.id, field_key)

        if self.driver.preview_panel.is_open:
            self.driver.preview_panel.update_widgets()
