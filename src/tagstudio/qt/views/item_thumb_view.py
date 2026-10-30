# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QBoxLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.platform_strings import open_file_str, trash_term
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.badge import Badge
from tagstudio.qt.views.styles.stylesheets import (
    HALF_PAD,
    boxed_label_style,
    item_thumb_filename_style,
)
from tagstudio.qt.views.styles.tag_icons import tag_icon

_ICON_SIZE = 24


class ItemThumbView(QVBoxLayout):
    FILE_LABEL_SPACING = 3

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
        self.ext_label.setStyleSheet(boxed_label_style())
        bottom_layout.addWidget(self.ext_label)
        bottom_layout.addStretch(2)

        # Count Label ----------------------------------------------------------
        # Used for Entry Group counts, video length, word count, etc.
        self.count_label = QLabel()
        self.count_label.setObjectName("countLabel")
        self.count_label.setText("-:--")
        self.count_label.setStyleSheet(boxed_label_style())
        bottom_layout.addWidget(self.count_label, alignment=Qt.AlignmentFlag.AlignBottom)
        top_layout.addStretch(2)

        # Tag Badge Checkboxes =================================================
        self.badge_container = QWidget()
        badge_layout = QHBoxLayout()
        badge_layout.setDirection(QBoxLayout.Direction.RightToLeft)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setSpacing(HALF_PAD)
        self.badge_container.setLayout(badge_layout)
        top_layout.addWidget(self.badge_container)

        self.badges: dict[int, Badge] = {}
        for tag_id in badge_tag_ids:
            badge = Badge(unwrap(tag_icon(tag_id)))
            badge.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            badge.setHidden(True)
            self.badges[tag_id] = badge
            badge_layout.addWidget(badge)

        # Filename Label =======================================================
        self.file_label = QLabel(Translations["generic.filename"])
        self.file_label.setStyleSheet(item_thumb_filename_style())

        self.addLayout(thumb_layout)
        self.addWidget(self.file_label, alignment=Qt.AlignmentFlag.AlignLeft)
