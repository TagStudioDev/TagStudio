# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PIL import ImageQt
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import auto_theme_overlay
from tagstudio.qt.views.styles.stylesheets import HALF_PAD

# TODO: There should be a global button theme somewhere.
_BUTTON_SIZE = 22
_ICON_MARGIN = 4
_ICON_SIZE = _BUTTON_SIZE - _ICON_MARGIN


class EntryDataBoxView(QVBoxLayout):
    _rm = ResourceManager()
    copy_icon = auto_theme_overlay(_rm.copy, inverse=True)
    edit_icon = auto_theme_overlay(_rm.edit, inverse=True)
    trash_icon = auto_theme_overlay(_rm.trash, inverse=True)

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        self.inner_layout = QVBoxLayout()
        self.inner_layout.setContentsMargins(HALF_PAD, 0, 0, HALF_PAD)
        self.inner_layout.setSpacing(0)
        self.field_container = QWidget()
        self.field_container.setLayout(self.inner_layout)
        self.addWidget(self.field_container)

        self.title_container = QWidget()
        self.title_layout = QHBoxLayout(self.title_container)
        self.title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_layout.setSpacing(0)
        self.inner_layout.addWidget(self.title_container)

        self.title_widget = QLabel()
        self.title_widget.setMinimumHeight(_BUTTON_SIZE)
        self.title_widget.setWordWrap(True)
        self.title_layout.addWidget(self.title_widget)
        self.title_layout.addStretch(2)

        self.copy_button = QPushButton()
        self.copy_button.setMinimumSize(_BUTTON_SIZE, _BUTTON_SIZE)
        self.copy_button.setMaximumSize(_BUTTON_SIZE, _BUTTON_SIZE)
        self.copy_button.setFlat(True)
        self.copy_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.copy_icon)))
        self.copy_button.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_layout.addWidget(self.copy_button)
        self.copy_button.setHidden(True)

        self.edit_button = QPushButton()
        self.edit_button.setMinimumSize(_BUTTON_SIZE, _BUTTON_SIZE)
        self.edit_button.setMaximumSize(_BUTTON_SIZE, _BUTTON_SIZE)
        self.edit_button.setFlat(True)
        self.edit_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.edit_icon)))
        self.edit_button.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_layout.addWidget(self.edit_button)
        self.edit_button.setHidden(True)

        self.remove_button = QPushButton()
        self.remove_button.setMinimumSize(_BUTTON_SIZE, _BUTTON_SIZE)
        self.remove_button.setMaximumSize(_BUTTON_SIZE, _BUTTON_SIZE)
        self.remove_button.setFlat(True)
        self.remove_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.trash_icon)))
        self.remove_button.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_layout.addWidget(self.remove_button)
        self.remove_button.setHidden(True)

        self.data = QWidget()
        self.data_layout = QHBoxLayout()
        self.data_layout.setContentsMargins(0, 0, 0, 0)
        self.data.setLayout(self.data_layout)
        self.inner_layout.addWidget(self.data)
