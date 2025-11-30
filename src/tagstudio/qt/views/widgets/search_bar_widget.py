import typing

from PIL import Image, ImageQt

from PIL import Image, ImageQt
from PySide6 import QtCore
from PySide6.QtCore import QMetaObject, QSize, QStringListModel, Qt, QEvent
from PySide6.QtGui import QAction, QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLayout,
    QPushButton,
    QCompleter,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QPushButton,
    QWidget,)


from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations
from tagstudio.qt.helpers.color_overlay import theme_fg_overlay

class SearchBarWidget(QWidget):
    back_button: QPushButton
    resource_manager: ResourceManager

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.resource_manager = ResourceManager()

        layout = QHBoxLayout()
        layout.setObjectName("search_bar_layout")
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.back_button = QPushButton(self)
        back_icon: Image.Image = self.resource_manager.get("bxs-left-arrow")  # pyright: ignore[reportAssignmentType]
        back_icon = theme_fg_overlay(back_icon, use_alpha=False)
        self.back_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(back_icon)))
        self.back_button.setObjectName("back_button")
        self.back_button.setMinimumSize(QSize(32, 32))
        self.back_button.setMaximumSize(QSize(32, 16777215))
        layout.addWidget(self.back_button)

        self.forward_button = QPushButton(self)
        forward_icon: Image.Image = self.resource_manager.get("bxs-right-arrow")  # pyright: ignore[reportAssignmentType]
        forward_icon = theme_fg_overlay(forward_icon, use_alpha=False)
        self.forward_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(forward_icon)))
        self.forward_button.setIconSize(QSize(16, 16))
        self.forward_button.setObjectName("forward_button")
        self.forward_button.setMinimumSize(QSize(32, 32))
        self.forward_button.setMaximumSize(QSize(32, 16777215))
        layout.addWidget(self.forward_button)

        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText(Translations["home.search_entries"])
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field_completion_list = QStringListModel()
        self.search_field_completer = QCompleter(
            self.search_field_completion_list, self.search_field
        )
        self.search_field_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_field.setCompleter(self.search_field_completer)
        layout.addWidget(self.search_field)

        self.search_button = QPushButton(Translations["home.search"], self)
        self.search_button.setObjectName("search_button")
        self.search_button.setMinimumSize(QSize(0, 32))
        layout.addWidget(self.search_button)

        self.setLayout(layout)
