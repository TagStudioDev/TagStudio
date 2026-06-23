# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.models.palette import ColorType, get_tag_color
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelWidget

if TYPE_CHECKING:
    from tagstudio.qt.controllers.search_panel_controller import SearchPanel

CREATE_BUTTON_STYLESHEET: str = f"""
    QPushButton{{
        background: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};
        color: {get_tag_color(ColorType.TEXT, TagColorEnum.DEFAULT)};
        font-weight: 600;
        border-color:{get_tag_color(ColorType.BORDER, TagColorEnum.DEFAULT)};
        border-radius: 6px;
        border-style: dashed;
        border-width: 2px;
        padding-right: 4px;
        padding-bottom: 1px;
        padding-left: 4px;
        font-size: 13px
    }}

    QPushButton::hover{{
        border-color: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};
    }}

    QPushButton::pressed{{
        background: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};
        color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};
        border-color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};
    }}

    QPushButton::focus{{
        border-color: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};
        outline: none;
    }}
"""


class SearchPanelView(PanelWidget):
    def __init__(self, is_chooser: bool) -> None:
        self.is_chooser: bool = is_chooser
        super().__init__()

        self.__root_layout = QVBoxLayout(self)
        self.__root_layout.setContentsMargins(6, 0, 6, 0)
        self.setMinimumSize(300, 400)

        # Limit container
        self.__limit_container = QWidget()
        self.__root_layout.addWidget(self.__limit_container)

        self.__limit_layout = QHBoxLayout(self.__limit_container)
        self.__limit_layout.setContentsMargins(0, 0, 0, 0)
        self.__limit_layout.setSpacing(12)
        self.__limit_layout.addStretch(1)

        self.__limit_title = QLabel(Translations["home.search.view_limit"])
        self.__limit_layout.addWidget(self.__limit_title)

        # Limit dropdown
        self.limit_combobox = QComboBox()
        self.__limit_layout.addWidget(self.limit_combobox)
        self.__limit_layout.addStretch(1)

        self.limit_combobox.setEditable(False)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setObjectName("search_field")
        self.__root_layout.addWidget(self.search_field)

        self.search_field.setMinimumSize(QSize(0, 32))

        # Scroll area
        self.__scroll_contents = QWidget()

        self._scroll_layout = QVBoxLayout(self.__scroll_contents)
        self._scroll_layout.setContentsMargins(6, 0, 6, 0)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__scroll_area = QScrollArea()
        self.__scroll_area.setWidget(self.__scroll_contents)
        self.__root_layout.addWidget(self.__scroll_area)

        self.__scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.__scroll_area.setWidgetResizable(True)
        self.__scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.__scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Create button
        self.create_button = QPushButton("")

        if not self.is_chooser:
            self.__root_layout.addWidget(self.create_button)

        # Create and add button
        self.create_and_add_button_in_layout: bool = False

        self.create_and_add_button = QPushButton()
        self.create_and_add_button.setFlat(True)
        self.create_and_add_button.setMinimumSize(22, 22)
        self.create_and_add_button.setStyleSheet(CREATE_BUTTON_STYLESHEET)

    @property
    def scroll_layout(self) -> QVBoxLayout:
        return self._scroll_layout

    @property
    def scroll_area(self) -> QScrollArea:
        return self.__scroll_area

    def connect_callbacks(self, controller: "SearchPanel[Any]") -> None:
        self.limit_combobox.currentIndexChanged.connect(controller.on_limit_changed)

        self.search_field.textChanged.connect(controller.on_search_query_changed)
        self.search_field.returnPressed.connect(
            lambda: controller.on_search_query_submitted(self.get_search_query())
        )

        self.create_button.clicked.connect(controller.on_item_create)
        self.create_and_add_button.clicked.connect(controller.on_item_create_and_add)

    def set_limit_items(self, limit_items: list[tuple[str, int]]) -> None:
        # Remove existing limit items
        for i in reversed(range(self.limit_combobox.count())):
            self.limit_combobox.removeItem(i)

        # Add new limit items
        self.limit_combobox.addItems([limit_item[0] for limit_item in limit_items])

    def get_limit_index(self) -> int:
        return self.limit_combobox.currentIndex()

    def set_limit_index(self, index: int) -> None:
        self.limit_combobox.setCurrentIndex(index)

    def focus_search_box(self, select_all: bool = False) -> None:
        self.search_field.setFocus()
        if select_all:
            self.search_field.selectAll()

    def get_search_query(self) -> str:
        return self.search_field.text()

    def clear_search_query(self) -> None:
        self.search_field.setText("")
        self.focus_search_box()

    # Item list
    def scroll_to(self, position: int) -> None:
        self.__scroll_area.verticalScrollBar().setValue(position)

    def get_item_widget(self, index: int, library: Library | None) -> Any:
        raise NotImplementedError()

    def add_create_and_add_button(self) -> None:
        if self.create_and_add_button_in_layout:
            return
        self._scroll_layout.addWidget(self.create_and_add_button)
        self.create_and_add_button.show()
        self.create_and_add_button_in_layout = True

    def remove_create_and_add_button(self) -> None:
        if not self.create_and_add_button_in_layout:
            return
        self._scroll_layout.removeWidget(self.create_and_add_button)
        self.create_and_add_button.hide()
        self.create_and_add_button_in_layout = False
