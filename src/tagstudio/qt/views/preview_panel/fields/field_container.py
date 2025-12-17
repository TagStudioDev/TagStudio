import math
from collections.abc import Callable
from pathlib import Path
from typing import override
from warnings import catch_warnings

from PIL import Image, ImageQt
from PySide6.QtCore import QEvent
from PySide6.QtGui import QEnterEvent, QPixmap, QResizeEvent, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.enums import Theme
from tagstudio.qt.views.preview_panel.fields.field_widget import FieldWidget

# TODO: reference a resources folder rather than path.parents[2]?
clipboard_icon_128: Image.Image = Image.open(
    str(Path(__file__).parents[4] / "resources/qt/images/clipboard_icon_128.png")
).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
clipboard_icon_128.load()

edit_icon_128: Image.Image = Image.open(
    str(Path(__file__).parents[4] / "resources/qt/images/edit_icon_128.png")
).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
edit_icon_128.load()

trash_icon_128: Image.Image = Image.open(
    str(Path(__file__).parents[4] / "resources/qt/images/trash_icon_128.png")
).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
trash_icon_128.load()

# TODO: There should be a global button theme somewhere.
CONTAINER_STYLE = f"""
    QWidget#fieldContainer{{
        border-radius: 4px;
    }}
    QWidget#fieldContainer::hover{{
        background-color: {Theme.COLOR_HOVER.value};
    }}
    QWidget#fieldContainer::pressed{{
        background-color: {Theme.COLOR_PRESSED.value};
    }}
"""

BUTTON_SIZE = 24

type Callback = Callable[[], None] | None


class FieldContainer(QWidget):
    """A container that holds a field widget and provides some relevant information and controls."""

    def __init__(self, title: str = "Field", inline: bool = True) -> None:
        super().__init__()

        self.__copy_callback: Callback = None
        self.__edit_callback: Callback = None
        self.__remove_callback: Callback = None

        # Container
        self.setObjectName("fieldContainer")
        self.title: str = title
        self.inline: bool = inline
        self.setStyleSheet(CONTAINER_STYLE)

        self.__root_layout = QVBoxLayout(self)
        self.__root_layout.setObjectName("baseLayout")
        self.__root_layout.setContentsMargins(0, 0, 0, 0)

        # Field container
        self.container_layout = QVBoxLayout()
        self.container_layout.setObjectName("fieldContainerLayout")
        self.container_layout.setContentsMargins(6, 0, 6, 6)
        self.container_layout.setSpacing(0)

        self.field_container = QWidget()
        self.field_container.setObjectName("fieldContainer")
        self.field_container.setLayout(self.container_layout)

        self.__root_layout.addWidget(self.field_container)

        # Title
        self.title_container = QWidget()
        self.title_layout = QHBoxLayout(self.title_container)
        self.title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.title_layout.setObjectName("titleLayout")
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_layout.setSpacing(0)

        self.container_layout.addWidget(self.title_container)

        self.title_label = QLabel()
        self.title_label.setMinimumHeight(BUTTON_SIZE)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setText(title)

        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch(2)

        # Copy button
        self.copy_button = QPushButton()
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setMinimumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.copy_button.setMaximumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.copy_button.setFlat(True)
        self.copy_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(clipboard_icon_128)))
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setHidden(True)

        self.title_layout.addWidget(self.copy_button)

        # Edit button
        self.edit_button = QPushButton()
        self.edit_button.setObjectName("editButton")
        self.edit_button.setMinimumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.edit_button.setMaximumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.edit_button.setFlat(True)
        self.edit_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(edit_icon_128)))
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_button.setHidden(True)

        self.title_layout.addWidget(self.edit_button)

        # Remove button
        self.remove_button = QPushButton()
        self.remove_button.setObjectName("removeButton")
        self.remove_button.setMinimumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.remove_button.setMaximumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.remove_button.setFlat(True)
        self.remove_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(trash_icon_128)))
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_button.setHidden(True)

        self.title_layout.addWidget(self.remove_button)

        # Field
        self.field = QWidget()
        self.field.setObjectName("field")
        self.field_layout = QHBoxLayout()
        self.field_layout.setObjectName("fieldLayout")
        self.field_layout.setContentsMargins(0, 0, 0, 0)
        self.field.setLayout(self.field_layout)

        self.container_layout.addWidget(self.field)

        # Fill data
        self.set_title(title)

    def set_title(self, title: str) -> None:
        """Sets the title of the field container."""
        self.title = self.title = f"<h4>{title}</h4>"
        self.title_label.setText(self.title)

    def set_inline(self, inline: bool) -> None:
        """Sets whether the field container is inline or not."""
        self.inline = inline

    def set_field_widget(self, widget: FieldWidget) -> None:
        """Sets the field widget the container holds."""
        if self.field_layout.itemAt(0):
            old: QWidget = self.field_layout.itemAt(0).widget()
            self.field_layout.removeWidget(old)
            old.deleteLater()

        self.field_layout.addWidget(widget)

    def get_field_widget(self) -> QWidget | None:
        """Returns the field widget the container holds."""
        if self.field_layout.itemAt(0):
            return self.field_layout.itemAt(0).widget()

        return None

    # Callbacks
    def set_copy_callback(self, callback: Callback = None) -> None:
        """Sets the callback to be called when the 'Copy' button is pressed."""
        with catch_warnings(record=True):
            self.copy_button.clicked.disconnect()

        self.__copy_callback = callback
        if callback:
            self.copy_button.clicked.connect(callback)

    def set_edit_callback(self, callback: Callback = None) -> None:
        """Sets the callback to be called when the 'Edit' button is pressed."""
        with catch_warnings(record=True):
            self.edit_button.clicked.disconnect()

        self.__edit_callback = callback
        if callback:
            self.edit_button.clicked.connect(callback)

    def set_remove_callback(self, callback: Callback = None) -> None:
        """Sets the callback to be called when the 'Remove' button is pressed."""
        with catch_warnings(record=True):
            self.remove_button.clicked.disconnect()

        self.__remove_callback = callback
        if callback:
            self.remove_button.clicked.connect(callback)

    # Events
    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.title_label.setFixedWidth(int(event.size().width() // 1.5))
        return super().resizeEvent(event)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        # NOTE: You could pass the hover event to the FieldWidget if needed.
        self.copy_button.setHidden(self.__copy_callback is None)
        self.edit_button.setHidden(self.__edit_callback is None)
        self.remove_button.setHidden(self.__remove_callback is None)

        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self.copy_button.setHidden(True)
        self.edit_button.setHidden(True)
        self.remove_button.setHidden(True)

        return super().leaveEvent(event)
