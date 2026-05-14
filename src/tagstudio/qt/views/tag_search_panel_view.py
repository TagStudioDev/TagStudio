# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

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
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.models.palette import ColorType, get_tag_color
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelWidget

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


class TagSearchPanelView(PanelWidget):
    def __init__(self, is_tag_chooser: bool) -> None:
        self.is_tag_chooser: bool = is_tag_chooser
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

        self.__limit_title = QLabel(Translations["tag.view_limit"])
        self.__limit_layout.addWidget(self.__limit_title)

        # Limit dropdown
        self.limit_combobox = QComboBox()
        self.__limit_layout.addWidget(self.limit_combobox)
        self.__limit_layout.addStretch(1)

        self.limit_combobox.setEditable(False)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setObjectName("searchField")
        self.__root_layout.addWidget(self.search_field)

        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field.setPlaceholderText(Translations["home.search_tags"])

        # Scroll area
        self.__scroll_contents = QWidget()

        self.__scroll_layout = QVBoxLayout(self.__scroll_contents)
        self.__scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.__scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__scroll_area = QScrollArea()
        self.__scroll_area.setWidget(self.__scroll_contents)
        self.__root_layout.addWidget(self.__scroll_area)

        self.__scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.__scroll_area.setWidgetResizable(True)
        self.__scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.__scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Create button
        self.create_button = QPushButton(Translations["tag.create"])

        if not self.is_tag_chooser:
            self.__root_layout.addWidget(self.create_button)

        # Create and add button
        self.create_and_add_button_in_layout: bool = False

        self.create_and_add_button = QPushButton()
        self.create_and_add_button.setFlat(True)
        self.create_and_add_button.setMinimumSize(22, 22)
        self.create_and_add_button.setStyleSheet(CREATE_BUTTON_STYLESHEET)

        self.__connect_callbacks()

    @property
    def scroll_layout(self) -> QVBoxLayout:
        return self.__scroll_layout

    @property
    def scroll_area(self) -> QScrollArea:
        return self.__scroll_area

    def __connect_callbacks(self):
        self.limit_combobox.currentIndexChanged.connect(self._on_limit_changed)

        self.search_field.textEdited.connect(self._on_search_query_changed)
        self.search_field.returnPressed.connect(
            lambda: self._on_search_query_submitted(self.get_search_query())
        )

        self.create_button.clicked.connect(self._on_tag_create)
        self.create_and_add_button.clicked.connect(self._on_tag_create_and_add)

    # Limit dropdown
    def _on_limit_changed(self, index: int) -> None:
        raise NotImplementedError()

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

    # Search field
    def _on_search_query_changed(self, query: str) -> None:
        raise NotImplementedError()

    def _on_search_query_submitted(self, query: str) -> None:
        raise NotImplementedError()

    def focus_search_box(self, select_all: bool = False):
        self.search_field.setFocus()
        if select_all:
            self.search_field.selectAll()

    def get_search_query(self) -> str:
        return self.search_field.text()

    def clear_search_query(self) -> None:
        self.search_field.setText("")
        self.focus_search_box()

    # Tag list
    def _on_tag_add(self) -> None:
        raise NotImplementedError()

    def scroll_to(self, position: int) -> None:
        self.__scroll_area.verticalScrollBar().setValue(position)

    def get_tag_widget(self, index: int, library: Library | None) -> TagWidget:
        """Gets the tag widget at a specific index."""
        # Create any new tag widgets needed up to the given index
        if self.__scroll_layout.count() <= index:
            while self.__scroll_layout.count() <= index:
                pad_tag_widget = TagWidget(
                    tag=None, has_edit=True, has_remove=True, library=library
                )
                pad_tag_widget.setHidden(True)
                self.__scroll_layout.addWidget(pad_tag_widget)

        tag_widget: QWidget = self.__scroll_layout.itemAt(index).widget()
        assert isinstance(tag_widget, TagWidget)
        return tag_widget

    # Create buttons
    def _on_tag_create(self) -> None:
        raise NotImplementedError()

    def _on_tag_create_and_add(self) -> None:
        raise NotImplementedError()

    def add_create_and_add_button(self) -> None:
        self.__scroll_layout.addWidget(self.create_and_add_button)
        self.create_and_add_button_in_layout = True

    def remove_create_and_add_button(self) -> None:
        if self.create_and_add_button_in_layout and self.__scroll_layout.count():
            self.__scroll_layout.removeWidget(self.create_and_add_button)
            self.create_and_add_button_in_layout = False
