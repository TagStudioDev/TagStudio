# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Iterable
from typing import NamedTuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QBoxLayout, QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.platform_strings import open_file_str, trash_term
from tagstudio.i18n.translations import Translations
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.stylesheets import (
    item_thumb_check_badge_style,
    item_thumb_filename_style,
    item_thumb_label_style,
)


class _BadgeStyle(NamedTuple):
    name: str
    icon: str
    icon_checked: str


_BADGE_STYLES: dict[int, _BadgeStyle] = {
    TAG_FAVORITE: _BadgeStyle("Favorite", "star_icon_empty", "star_icon_filled"),
    TAG_ARCHIVED: _BadgeStyle("Archived", "box_icon_empty", "box_icon_filled"),
}

_ICON_SIZE = 24


class ItemThumbView(QVBoxLayout):
    FILE_LABEL_HEIGHT = 12
    FILE_LABEL_SPACING = 4

    def __init__(self, badge_tag_ids: Iterable[int]) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(self.FILE_LABEL_SPACING)

        # +----------+
        # |   ARC FAV| Top Right: Favorite & Archived Badges
        # |          |
        # |          |
        # |EXT      #| Lower Left: File Type or Entry Group Icon
        # +----------+ Lower Right: Entry Group Count, Video Length, or Word Count
        #
        #   Filename   Underneath: (Optional) Filename

        # Thumbnail ============================================================

        # +----------+
        # |*--------*|
        # ||        ||
        # ||        ||
        # |*--------*|
        # +----------+
        thumb_layout = QVBoxLayout()
        thumb_layout.setObjectName("baseLayout")
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        # +----------+
        # |[~~~~~~~~]|
        # |          |
        # |          |
        # |          |
        # +----------+
        top_layout = QHBoxLayout()
        top_layout.setObjectName("topLayout")
        top_layout.setContentsMargins(6, 6, 6, 6)
        thumb_layout.addLayout(top_layout)

        # +----------+
        # |[~~~~~~~~]|
        # |     ^    |
        # |     |    |
        # |     v    |
        # +----------+
        thumb_layout.addStretch(2)

        # +----------+
        # |[~~~~~~~~]|
        # |     ^    |
        # |     v    |
        # |[~~~~~~~~]|
        # +----------+
        bottom_layout = QHBoxLayout()
        bottom_layout.setObjectName("bottomLayout")
        bottom_layout.setContentsMargins(6, 6, 6, 6)
        thumb_layout.addLayout(bottom_layout)

        self.open_file_action = QAction(Translations["file.open_file"], self)
        self.open_explorer_action = QAction(open_file_str(), self)
        self.delete_action = QAction(
            Translations.format("trash.context.ambiguous", trash_term=trash_term()), self
        )

        # Static Labels ========================================================

        # Item Type Icon -------------------------------------------------------
        # Used for showing the Entry Group icons.
        # Mutually exclusive with the File Extension Label.
        self.item_type_icon = QLabel()
        self.item_type_icon.setObjectName("itemTypeIcon")
        self.item_type_icon.setMinimumSize(_ICON_SIZE, _ICON_SIZE)
        self.item_type_icon.setMaximumSize(_ICON_SIZE, _ICON_SIZE)
        bottom_layout.addWidget(self.item_type_icon)

        # File Extension Label -------------------------------------------------
        # Mutually exclusive with the Item Type Icon.
        self.ext_label = QLabel()
        self.ext_label.setObjectName("extLabel")
        self.ext_label.setStyleSheet(item_thumb_label_style())
        bottom_layout.addWidget(self.ext_label)
        bottom_layout.addStretch(2)

        # Count Label ----------------------------------------------------------
        # Used for Entry Group counts, video length, word count, etc.
        self.count_label = QLabel()
        self.count_label.setObjectName("countLabel")
        self.count_label.setText("-:--")
        self.count_label.setStyleSheet(item_thumb_label_style())
        bottom_layout.addWidget(self.count_label, alignment=Qt.AlignmentFlag.AlignBottom)
        top_layout.addStretch(2)

        # Tag Badge Checkboxes =================================================
        self.badge_container = QWidget()
        badge_layout = QHBoxLayout()
        badge_layout.setDirection(QBoxLayout.Direction.RightToLeft)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setSpacing(6)
        self.badge_container.setLayout(badge_layout)
        top_layout.addWidget(self.badge_container)

        rm = ResourceManager()
        self.badges: dict[int, QCheckBox] = {}
        for tag_id in badge_tag_ids:
            style = _BADGE_STYLES[tag_id]
            badge = QCheckBox()
            badge.setObjectName(f"{style.name.lower()}_badge")
            badge.setToolTip(style.name)
            badge.setStyleSheet(
                item_thumb_check_badge_style(
                    _ICON_SIZE,
                    unwrap(rm.get_path(style.icon)),
                    unwrap(rm.get_path(style.icon_checked)),
                )
            )
            badge.setMinimumSize(_ICON_SIZE, _ICON_SIZE)
            badge.setMaximumSize(_ICON_SIZE, _ICON_SIZE)
            badge.setHidden(True)
            self.badges[tag_id] = badge
            badge_layout.addWidget(badge)

        # Filename Label =======================================================
        self.file_label = QLabel(Translations["generic.filename"])
        self.file_label.setStyleSheet(item_thumb_filename_style())

        self.addLayout(thumb_layout)
        self.addWidget(self.file_label, alignment=Qt.AlignmentFlag.AlignLeft)
