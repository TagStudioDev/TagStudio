import math
import typing
from pathlib import Path
from typing import override

from PIL import Image, ImageQt
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tagstudio.core.enums import Theme

if typing.TYPE_CHECKING:
    from tagstudio.qt.views.field_widget_view import FieldWidgetView

# TODO: reference a resources folder rather than path.parents[2]?
clipboard_icon_128: Image.Image = Image.open(
    str(Path(__file__).parents[2] / "resources/qt/images/clipboard_icon_128.png")
).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
clipboard_icon_128.load()

edit_icon_128: Image.Image = Image.open(
    str(Path(__file__).parents[2] / "resources/qt/images/edit_icon_128.png")
).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
edit_icon_128.load()

trash_icon_128: Image.Image = Image.open(
    str(Path(__file__).parents[2] / "resources/qt/images/trash_icon_128.png")
).resize((math.floor(24 * 1.25), math.floor(24 * 1.25)))
trash_icon_128.load()

# TODO: There should be a global button theme somewhere.
CONTAINER_STYLE = f"""
    QWidget#field_container{{
        border-radius: 4px;
    }}
    
    QWidget#field_container::hover{{
        background-color: {Theme.COLOR_HOVER.value};
    }}
    
    QWidget#field_container::pressed{{
        background-color: {Theme.COLOR_PRESSED.value};
    }}
"""

BUTTON_SIZE: int = 24


class FieldContainerView(QWidget):
    """A container that holds a field widget and provides some relevant information and controls."""

    def __init__(self, title: str = "Field", inline: bool = True) -> None:
        super().__init__()

        self.copy_enabled: bool = False
        self.edit_enabled: bool = False
        self.remove_enabled: bool = False

        self.setStyleSheet(CONTAINER_STYLE)

        # Container
        self.setObjectName("field_container")
        self.title: str = title
        self.inline: bool = inline

        self.__root_layout = QVBoxLayout(self)
        self.__root_layout.setObjectName("root_layout")
        self.__root_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__root_layout)

        # Field container
        self.__container_layout = QVBoxLayout()
        self.__container_layout.setObjectName("field_container_layout")
        self.__container_layout.setContentsMargins(6, 0, 6, 6)
        self.__container_layout.setSpacing(0)

        self.__field_container = QWidget()
        self.__field_container.setObjectName("field_container")
        self.__field_container.setLayout(self.__container_layout)

        self.__root_layout.addWidget(self.__field_container)

        # Title
        self.__title_container = QWidget()
        self.__title_layout = QHBoxLayout(self.__title_container)
        self.__title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__title_layout.setObjectName("title_layout")
        self.__title_layout.setContentsMargins(0, 0, 0, 0)
        self.__title_layout.setSpacing(0)

        self.__container_layout.addWidget(self.__title_container)

        self.__title_label = QLabel()
        self.__title_label.setMinimumHeight(BUTTON_SIZE)
        self.__title_label.setObjectName("field_title")
        self.__title_label.setWordWrap(True)
        self.__title_label.setText(title)

        self.__title_layout.addWidget(self.__title_label)
        self.__title_layout.addStretch(2)

        # Copy button
        self.__copy_button = QPushButton()
        self.__copy_button.setObjectName("copy_button")
        self.__copy_button.setMinimumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.__copy_button.setMaximumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.__copy_button.setFlat(True)
        self.__copy_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(clipboard_icon_128)))
        self.__copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.__copy_button.setHidden(True)

        self.__title_layout.addWidget(self.__copy_button)

        # Edit button
        self.__edit_button = QPushButton()
        self.__edit_button.setObjectName("edit_button")
        self.__edit_button.setMinimumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.__edit_button.setMaximumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.__edit_button.setFlat(True)
        self.__edit_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(edit_icon_128)))
        self.__edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.__edit_button.setHidden(True)

        self.__title_layout.addWidget(self.__edit_button)

        # Remove button
        self.__remove_button = QPushButton()
        self.__remove_button.setObjectName("remove_button")
        self.__remove_button.setMinimumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.__remove_button.setMaximumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.__remove_button.setFlat(True)
        self.__remove_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(trash_icon_128)))
        self.__remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.__remove_button.setHidden(True)

        self.__title_layout.addWidget(self.__remove_button)

        # Field
        self.__field = QWidget()
        self.__field.setObjectName("field")

        self.__field_layout = QHBoxLayout()
        self.__field_layout.setObjectName("field_layout")
        self.__field_layout.setContentsMargins(0, 0, 0, 0)
        self.__field.setLayout(self.__field_layout)

        self.__container_layout.addWidget(self.__field)

        self.set_title(title)

        self.__connect_callbacks()

    def __connect_callbacks(self) -> None:
        self.__copy_button.clicked.connect(self._copy_callback)
        self.__edit_button.clicked.connect(self._edit_callback)
        self.__remove_button.clicked.connect(self._remove_callback)

    def _copy_callback(self) -> None:
        raise NotImplementedError()

    def _edit_callback(self) -> None:
        raise NotImplementedError()

    def _remove_callback(self) -> None:
        raise NotImplementedError()

    def set_field_widget(self, widget: "FieldWidgetView") -> None:
        """Sets the field widget the container holds."""
        if self.__field_layout.itemAt(0):
            old: QWidget = self.__field_layout.itemAt(0).widget()
            self.__field_layout.removeWidget(old)
            old.deleteLater()

        self.__field_layout.addWidget(widget)

    def get_field_widget(self) -> QWidget | None:
        """Returns the field widget the container holds."""
        if self.__field_layout.itemAt(0):
            return self.__field_layout.itemAt(0).widget()
        return None

    def set_title(self, title: str) -> None:
        """Sets the title of the field container."""
        self.title = f"<h4>{title}</h4>"
        self.__title_label.setText(self.title)

    def set_inline(self, inline: bool) -> None:
        """Sets whether the field container is inline or not."""
        self.inline = inline

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        # NOTE: You could pass the hover event to the FieldWidgetView if needed.
        self.__copy_button.setHidden(not self.copy_enabled)
        self.__edit_button.setHidden(not self.edit_enabled)
        self.__remove_button.setHidden(not self.remove_enabled)

        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self.__copy_button.setHidden(True)
        self.__edit_button.setHidden(True)
        self.__remove_button.setHidden(True)

        return super().leaveEvent(event)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.__title_label.setFixedWidth(int(event.size().width() // 1.5))
        return super().resizeEvent(event)
