# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
import typing

import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSplitter, QVBoxLayout, QWidget

from tagstudio.core.constants import FFMPEG_HELP_URL
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.field_suggest_box import FieldSuggestBox
from tagstudio.qt.controllers.preview_thumb import PreviewThumb
from tagstudio.qt.controllers.return_button import ReturnButton
from tagstudio.qt.controllers.tag_suggest_box import TagSuggestBox
from tagstudio.qt.controllers.tiles.tile_list import TileList
from tagstudio.qt.mixed.file_attributes import FileAttributes
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.stylesheets import (
    HALF_PAD,
    PAD,
    WIN_PAD,
    button_style,
    preview_warning_style,
)

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)


class InspectorView(QVBoxLayout):
    def __init__(self, driver: QtDriver, pixel_ratio: float) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, WIN_PAD, WIN_PAD)
        self.setSpacing(PAD)
        rm = ResourceManager()

        # Search/Create Boxes
        def ph_text(key: str) -> str:
            return " ".join([Translations[key], Translations["home.search.how_to_exit"]])

        self.field_search_box = FieldSuggestBox(
            driver.lib, driver.settings, ph_text("home.search_or_create_fields")
        )
        self.tag_search_box = TagSuggestBox(
            driver.lib, driver.settings, ph_text("home.search_or_create_tags")
        )

        self.preview_thumb = PreviewThumb(driver.lib, driver)
        self.file_attrs = FileAttributes(driver.lib, driver)
        self.containers = TileList(driver.lib, driver)

        # Visual Preview
        preview_section = QWidget()
        preview_layout = QVBoxLayout(preview_section)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(PAD)

        # Warning Banner (Missing FFmpeg, etc.)
        self.warning_banner = QWidget()
        self.warning_banner.setObjectName("ffmpeg_widget")
        ffmpeg_warning_layout = QHBoxLayout(self.warning_banner)
        ffmpeg_warning_layout.setContentsMargins(HALF_PAD, HALF_PAD, HALF_PAD, HALF_PAD)
        self.warning_banner.setStyleSheet(preview_warning_style())
        ffmpeg_warning_label = QLabel(
            Translations.format(
                "preview.missing_module.multimedia",
                module=f'<a href="{FFMPEG_HELP_URL}">FFmpeg</a>',
            )
        )
        ffmpeg_warning_label.setWordWrap(True)
        ffmpeg_warning_label.linkActivated.connect(
            lambda x: QDesktopServices.openUrl(FFMPEG_HELP_URL)
        )
        warning_icon = QLabel()
        warning_icon_pixmap = rm.alert.scaled(
            math.floor(20 * pixel_ratio), math.floor(20 * pixel_ratio)
        )
        warning_icon_pixmap.setDevicePixelRatio(pixel_ratio)
        warning_icon.setPixmap(warning_icon_pixmap)
        ffmpeg_warning_layout.addWidget(warning_icon)
        ffmpeg_warning_layout.addWidget(ffmpeg_warning_label)
        ffmpeg_warning_layout.setStretch(1, 1)
        self.warning_banner.hide()

        # File Information
        info_section = QWidget()
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(PAD)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Vertical)
        splitter.setHandleWidth(PAD * 2)

        # Add Tag/Field Buttons
        add_buttons_container = QWidget()
        add_buttons_layout = QHBoxLayout(add_buttons_container)
        add_buttons_layout.setContentsMargins(0, 0, 0, 0)
        add_buttons_layout.setSpacing(PAD)

        self.add_tag_button = ReturnButton(Translations["tag.add"])
        self.add_tag_button.setEnabled(False)
        self.add_tag_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_tag_button.setMinimumHeight(30)
        self.add_tag_button.setStyleSheet(button_style())

        self.add_field_button = ReturnButton(Translations["field.add"])
        self.add_field_button.setEnabled(False)
        self.add_field_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_field_button.setMinimumHeight(30)
        self.add_field_button.setStyleSheet(button_style())

        add_buttons_layout.addWidget(self.add_tag_button)
        add_buttons_layout.addWidget(self.add_field_button)
        add_buttons_layout.addWidget(self.tag_search_box)
        add_buttons_layout.addWidget(self.field_search_box)

        # Finalize Layout
        preview_layout.addWidget(self.preview_thumb)
        info_layout.addWidget(self.warning_banner)
        info_layout.addWidget(self.file_attrs)
        info_layout.addWidget(self.containers)

        splitter.addWidget(preview_section)
        splitter.addWidget(info_section)
        splitter.setStretchFactor(1, 2)

        self.addWidget(splitter)
        self.addWidget(add_buttons_container)
