# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import sys

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library, Tag
from src.core.library.alchemy.enums import TagColor
from src.core.palette import ColorType, get_tag_color
from src.qt.modals.tag_search import TagSearchPanel
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import TagWidget

logger = structlog.get_logger(__name__)


class BuildTagPanel(PanelWidget):
    on_edit = Signal(Tag)

    def __init__(self, library: Library, tag: Tag | None = None):
        super().__init__()
        self.lib = library

        self.setMinimumSize(300, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Name -----------------------------------------------------------------
        self.name_widget = QWidget()
        self.name_layout = QVBoxLayout(self.name_widget)
        self.name_layout.setStretch(1, 1)
        self.name_layout.setContentsMargins(0, 0, 0, 0)
        self.name_layout.setSpacing(0)
        self.name_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.name_title = QLabel()
        self.name_title.setText("Name")
        self.name_layout.addWidget(self.name_title)
        self.name_field = QLineEdit()
        self.name_layout.addWidget(self.name_field)

        # Shorthand ------------------------------------------------------------
        self.shorthand_widget = QWidget()
        self.shorthand_layout = QVBoxLayout(self.shorthand_widget)
        self.shorthand_layout.setStretch(1, 1)
        self.shorthand_layout.setContentsMargins(0, 0, 0, 0)
        self.shorthand_layout.setSpacing(0)
        self.shorthand_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.shorthand_title = QLabel()
        self.shorthand_title.setText("Shorthand")
        self.shorthand_layout.addWidget(self.shorthand_title)
        self.shorthand_field = QLineEdit()
        self.shorthand_layout.addWidget(self.shorthand_field)

        # Aliases --------------------------------------------------------------
        self.aliases_widget = QWidget()
        self.aliases_layout = QVBoxLayout(self.aliases_widget)
        self.aliases_layout.setStretch(1, 1)
        self.aliases_layout.setContentsMargins(0, 0, 0, 0)
        self.aliases_layout.setSpacing(0)
        self.aliases_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.aliases_title = QLabel()
        self.aliases_title.setText("Aliases")
        self.aliases_layout.addWidget(self.aliases_title)

        self.aliases_table = QTableWidget(0, 2)
        self.aliases_table.horizontalHeader().setVisible(False)
        self.aliases_table.verticalHeader().setVisible(False)
        self.aliases_table.horizontalHeader().setStretchLastSection(True)
        self.aliases_table.setColumnWidth(0, 35)

        self.alias_add_button = QPushButton()
        self.alias_add_button.setText("+")

        self.alias_add_button.clicked.connect(lambda: self.add_alias_callback())

        # Subtags ------------------------------------------------------------

        self.subtags_widget = QWidget()
        self.subtags_layout = QVBoxLayout(self.subtags_widget)
        self.subtags_layout.setStretch(1, 1)
        self.subtags_layout.setContentsMargins(0, 0, 0, 0)
        self.subtags_layout.setSpacing(0)
        self.subtags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.subtags_title = QLabel()
        self.subtags_title.setText("Parent Tags")
        self.subtags_layout.addWidget(self.subtags_title)

        self.scroll_contents = QWidget()
        self.subtags_scroll_layout = QVBoxLayout(self.scroll_contents)
        self.subtags_scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.subtags_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        # self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.scroll_contents)
        # self.scroll_area.setMinimumHeight(60)

        self.subtags_layout.addWidget(self.scroll_area)

        self.subtags_add_button = QPushButton()
        self.subtags_add_button.setText("+")
        tsp = TagSearchPanel(self.lib)
        tsp.tag_chosen.connect(lambda x: self.add_subtag_callback(x))
        self.add_tag_modal = PanelModal(tsp, "Add Parent Tags", "Add Parent Tags")
        self.subtags_add_button.clicked.connect(self.add_tag_modal.show)
        self.subtags_layout.addWidget(self.subtags_add_button)

        exclude_ids: list[int] = list()
        if tag is not None:
            exclude_ids.append(tag.id)

        tsp = TagSearchPanel(self.lib, exclude_ids)
        tsp.tag_chosen.connect(lambda x: self.add_subtag_callback(x))
        self.add_tag_modal = PanelModal(tsp, "Add Parent Tags", "Add Parent Tags")
        self.subtags_add_button.clicked.connect(self.add_tag_modal.show)

        # Shorthand ------------------------------------------------------------
        self.color_widget = QWidget()
        self.color_layout = QVBoxLayout(self.color_widget)
        self.color_layout.setStretch(1, 1)
        self.color_layout.setContentsMargins(0, 0, 0, 0)
        self.color_layout.setSpacing(0)
        self.color_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.color_title = QLabel()
        self.color_title.setText("Color")
        self.color_layout.addWidget(self.color_title)
        self.color_field = QComboBox()
        self.color_field.setEditable(False)
        self.color_field.setMaxVisibleItems(10)
        self.color_field.setStyleSheet("combobox-popup:0;")
        for color in TagColor:
            self.color_field.addItem(color.name, userData=color.value)
        self.color_field.currentIndexChanged.connect(
            lambda c: (
                self.color_field.setStyleSheet(
                    "combobox-popup:0;"
                    "font-weight:600;"
                    f"color:{get_tag_color(ColorType.TEXT, self.color_field.currentData())};"
                    f"background-color:{get_tag_color(
                        ColorType.PRIMARY,
                        self.color_field.currentData())};"
                )
            )
        )
        self.color_layout.addWidget(self.color_field)

        # Add Widgets to Layout ================================================
        self.root_layout.addWidget(self.name_widget)
        self.root_layout.addWidget(self.shorthand_widget)
        self.root_layout.addWidget(self.aliases_widget)
        self.root_layout.addWidget(self.aliases_table)
        self.root_layout.addWidget(self.alias_add_button)
        self.root_layout.addWidget(self.subtags_widget)
        self.root_layout.addWidget(self.color_widget)

        self.subtag_ids: set[int] = set()
        self.alias_ids: set[int] = set()
        self.alias_names: set[str] = set()
        self.new_alias_names: dict = dict()
        self.new_item_id = sys.maxsize

        self.set_tag(tag or Tag(name="New Tag"))

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:  # type: ignore
            focused_widget = QApplication.focusWidget()
            if isinstance(focused_widget, QTableWidget):
                self.add_alias_callback()

        if event.key() == Qt.Key_Backspace:  # type: ignore
            focused_widget = QApplication.focusWidget()
            row = self.aliases_table.rowCount() - 1
            is_table = isinstance(focused_widget, QTableWidget)
            is_empty = self.aliases_table.item(row, 1).text().strip() == ""
            if is_table and is_empty:
                button = self.aliases_table.cellWidget(row, 0)

                if button and isinstance(button, QPushButton):
                    button.click()
                    self.aliases_table.setCurrentCell(row - 1, 0)

    def add_subtag_callback(self, tag_id: int):
        logger.info("add_subtag_callback", tag_id=tag_id)
        self.subtag_ids.add(tag_id)
        self.set_subtags()

    def remove_subtag_callback(self, tag_id: int):
        logger.info("removing subtag", tag_id=tag_id)
        self.subtag_ids.remove(tag_id)
        self.set_subtags()

    def add_alias_callback(self):
        logger.info("add_alias_callback")

        id = self.new_item_id

        self.alias_ids.add(id)
        self.new_alias_names[id] = ""

        self.new_item_id -= 1

        self._set_aliases()

    def remove_alias_callback(self, alias_name: str, alias_id: int | None = None):
        logger.info("remove_alias_callback")
        self.alias_ids.remove(alias_id)
        self._set_aliases()

    def set_subtags(self):
        while self.subtags_scroll_layout.itemAt(0):
            self.subtags_scroll_layout.takeAt(0).widget().deleteLater()

        c = QWidget()
        layout = QVBoxLayout(c)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        for tag_id in self.subtag_ids:
            tag = self.lib.get_tag(tag_id)
            tw = TagWidget(tag, has_edit=False, has_remove=True)
            tw.on_remove.connect(lambda t=tag_id: self.remove_subtag_callback(t))
            layout.addWidget(tw)
        self.subtags_scroll_layout.addWidget(c)

    def add_aliases(self):
        names: set[str] = set()
        for i in range(0, self.aliases_table.rowCount()):
            widget = self.aliases_table.item(i, 1)

            names.add(widget.text())

        remove: set[str] = self.alias_names - names

        self.alias_names = self.alias_names - remove

        for name in names:
            # add new aliases
            if name != "":
                self.alias_names.add(name)

    def _update_new_alias_name_dict(self):
        row = self.aliases_table.rowCount()
        logger.info(row)
        for i in range(0, self.aliases_table.rowCount()):
            widget = self.aliases_table.item(i, 1)
            self.new_alias_names[widget.data(Qt.UserRole)] = widget.text()  # type: ignore

    def _set_aliases(self):
        self._update_new_alias_name_dict()

        while self.aliases_table.rowCount() > 0:
            self.aliases_table.removeRow(0)

        self.alias_names.clear()

        for alias_id in list(self.alias_ids)[::-1]:
            alias = self.lib.get_alias(self.tag.id, alias_id)

            alias_name = alias.name if alias else self.new_alias_names[alias_id]

            self.alias_names.add(alias_name)

            remove_btn = QPushButton("-")
            remove_btn.clicked.connect(
                lambda a=alias_name, id=alias_id: self.remove_alias_callback(a, id)
            )

            row = self.aliases_table.rowCount()
            new_item = QTableWidgetItem(alias_name)
            new_item.setData(Qt.UserRole, alias_id)  # type: ignore

            self.aliases_table.insertRow(row)
            self.aliases_table.setItem(row, 1, new_item)
            self.aliases_table.setCellWidget(row, 0, remove_btn)

    def set_tag(self, tag: Tag):
        self.tag = tag

        self.tag = tag

        logger.info("setting tag", tag=tag)

        self.name_field.setText(tag.name)
        self.shorthand_field.setText(tag.shorthand or "")

        for alias_id in tag.alias_ids:
            self.alias_ids.add(alias_id)

        self._set_aliases()

        for subtag in tag.subtag_ids:
            self.subtag_ids.add(subtag)

        self.set_subtags()

        # select item in self.color_field where the userData value matched tag.color
        for i in range(self.color_field.count()):
            if self.color_field.itemData(i) == tag.color:
                self.color_field.setCurrentIndex(i)
                break

    def build_tag(self) -> Tag:
        color = self.color_field.currentData() or TagColor.DEFAULT

        tag = self.tag

        self.add_aliases()

        tag.name = self.name_field.text()
        tag.shorthand = self.shorthand_field.text()
        tag.color = color

        logger.info("built tag", tag=tag)
        return tag
