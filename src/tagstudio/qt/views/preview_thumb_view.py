# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedLayout, QWidget

from tagstudio.i18n.platform_strings import open_file_str, trash_term
from tagstudio.i18n.translations import Translations
from tagstudio.qt.mixed.media_player import MediaPlayer

if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

_DEFAULT_PREVIEW_SIZE = (272, 272)


class PreviewThumbView(QStackedLayout):
    """The layout for the file preview thumbnail widget."""

    def __init__(self, driver: QtDriver) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.setContentsMargins(0, 0, 0, 0)

        self.open_file_action = QAction(Translations["file.open_file"], self)
        self.open_explorer_action = QAction(open_file_str(), self)
        self.delete_action = QAction(
            Translations.format("trash.context.singular", trash_term=trash_term()), self
        )

        self.button_wrapper = QPushButton()
        self.button_wrapper.setMinimumSize(*_DEFAULT_PREVIEW_SIZE)
        self.button_wrapper.setFlat(True)
        self.button_wrapper.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.button_wrapper.addAction(self.open_file_action)
        self.button_wrapper.addAction(self.open_explorer_action)
        self.button_wrapper.addAction(self.delete_action)

        # In testing, it didn't seem possible to center the widgets directly
        # on the QStackedLayout. Adding sublayouts allows us to center the widgets.
        self.preview_img_page = QWidget()
        self._stacked_page_setup(self.preview_img_page, self.button_wrapper)

        self.preview_gif = QLabel()
        self.preview_gif.setMinimumSize(*_DEFAULT_PREVIEW_SIZE)
        self.preview_gif.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.preview_gif.setCursor(Qt.CursorShape.ArrowCursor)
        self.preview_gif.addAction(self.open_file_action)
        self.preview_gif.addAction(self.open_explorer_action)
        self.preview_gif.addAction(self.delete_action)

        self.preview_gif_page = QWidget()
        self._stacked_page_setup(self.preview_gif_page, self.preview_gif)

        self.media_player = MediaPlayer(driver)
        self.media_player.addAction(self.open_file_action)
        self.media_player.addAction(self.open_explorer_action)
        self.media_player.addAction(self.delete_action)

        self.media_player_page = QWidget()
        self._stacked_page_setup(self.media_player_page, self.media_player)

        self.addWidget(self.preview_img_page)
        self.addWidget(self.preview_gif_page)
        self.addWidget(self.media_player_page)

    def _stacked_page_setup(self, page: QWidget, widget: QWidget) -> None:
        layout = QHBoxLayout(page)
        layout.addWidget(widget)
        layout.setAlignment(widget, Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        page.setLayout(layout)
