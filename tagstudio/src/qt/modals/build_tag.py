# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import sys
from typing import cast

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
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library, Tag
from src.core.library.alchemy.enums import TagColor
from src.core.palette import ColorType, UiColor, get_tag_color, get_ui_color
from src.qt.modals.tag_search import TagSearchPanel
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import TagWidget

logger = structlog.get_logger(__name__)


class CustomTableItem(QLineEdit):
    def __init__(self, text, on_return, on_backspace, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.on_return = on_return
        self.on_backspace = on_backspace

    def set_id(self, id):
        self.id = id

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.on_return()
        elif event.key() == Qt.Key.Key_Backspace and self.text().strip() == "":
            self.on_backspace()
        else:
            super().keyPressEvent(event)


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
        self.name_field.setFixedHeight(24)
        self.name_field.textChanged.connect(self.on_name_changed)
        self.name_field.setPlaceholderText("Tag Name (Required)")
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

        self.alias_add_button.clicked.connect(self.add_alias_callback)

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
        self.subtags_add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.subtags_add_button.setText("+")
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
            self.color_field.addItem(color.name.replace("_", " ").title(), userData=color.value)
        # self.color_field.setProperty("appearance", "flat")
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

        self.subtag_ids: list[int] = list()
        self.alias_ids: list[int] = list()
        self.alias_names: list[str] = list()
        self.new_alias_names: dict = dict()
        self.new_item_id = sys.maxsize

        self.set_tag(tag or Tag(name="New Tag"))
        if tag is None:
            self.name_field.selectAll()

    def backspace(self):
        focused_widget = QApplication.focusWidget()
        row = self.aliases_table.rowCount()

        if isinstance(focused_widget, CustomTableItem) is False:
            return
        remove_row = 0
        for i in range(0, row):
            item = self.aliases_table.cellWidget(i, 1)
            if (
                isinstance(item, CustomTableItem)
                and cast(CustomTableItem, item).id == cast(CustomTableItem, focused_widget).id
            ):
                cast(QPushButton, self.aliases_table.cellWidget(i, 0)).click()
                remove_row = i
                break

        if self.aliases_table.rowCount() <= 0:
            return

        if remove_row == 0:
            remove_row = 1

        self.aliases_table.cellWidget(remove_row - 1, 1).setFocus()

    def enter(self):
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, CustomTableItem):
            self.add_alias_callback()

    def add_subtag_callback(self, tag_id: int):
        logger.info("add_subtag_callback", tag_id=tag_id)
        self.subtag_ids.append(tag_id)
        self.set_subtags()

    def remove_subtag_callback(self, tag_id: int):
        logger.info("removing subtag", tag_id=tag_id)
        self.subtag_ids.remove(tag_id)
        self.set_subtags()

    def add_alias_callback(self):
        logger.info("add_alias_callback")

        id = self.new_item_id

        self.alias_ids.append(id)
        self.new_alias_names[id] = ""

        self.new_item_id -= 1

        self._set_aliases()

        row = self.aliases_table.rowCount() - 1
        item = self.aliases_table.cellWidget(row, 1)
        item.setFocus()

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
            widget = self.aliases_table.cellWidget(i, 1)

            names.add(cast(CustomTableItem, widget).text())

        remove: set[str] = set(self.alias_names) - names

        self.alias_names = list(set(self.alias_names) - remove)

        for name in names:
            # add new aliases
            if name.strip() != "" and name not in set(self.alias_names):
                self.alias_names.append(name)

    def _update_new_alias_name_dict(self):
        row = self.aliases_table.rowCount()
        logger.info(row)
        for i in range(0, self.aliases_table.rowCount()):
            widget = self.aliases_table.cellWidget(i, 1)
            self.new_alias_names[widget.id] = widget.text()  # type: ignore

    def _set_aliases(self):
        self._update_new_alias_name_dict()

        while self.aliases_table.rowCount() > 0:
            self.aliases_table.removeRow(0)

        self.alias_names.clear()

        for alias_id in self.alias_ids:
            alias = self.lib.get_alias(self.tag.id, alias_id)

            alias_name = alias.name if alias else self.new_alias_names[alias_id]

            self.alias_names.append(alias_name)

            remove_btn = QPushButton("-")
            remove_btn.clicked.connect(
                lambda a=alias_name, id=alias_id: self.remove_alias_callback(a, id)
            )

            row = self.aliases_table.rowCount()
            new_item = CustomTableItem(alias_name, self.enter, self.backspace)
            new_item.set_id(alias_id)

            self.aliases_table.insertRow(row)
            self.aliases_table.setCellWidget(row, 1, new_item)
            self.aliases_table.setCellWidget(row, 0, remove_btn)

    def set_tag(self, tag: Tag):
        self.tag = tag

        self.tag = tag

        logger.info("setting tag", tag=tag)

        self.name_field.setText(tag.name)
        self.shorthand_field.setText(tag.shorthand or "")

        for alias_id in tag.alias_ids:
            self.alias_ids.append(alias_id)

        self._set_aliases()

        for subtag in tag.subtag_ids:
            self.subtag_ids.append(subtag)

        self.set_subtags()

        # select item in self.color_field where the userData value matched tag.color
        for i in range(self.color_field.count()):
            if self.color_field.itemData(i) == tag.color:
                self.color_field.setCurrentIndex(i)
                break

    def on_name_changed(self):
        is_empty = not self.name_field.text().strip()

        self.name_field.setStyleSheet(
            f"border: 1px solid {get_ui_color(ColorType.PRIMARY, UiColor.RED)}; border-radius: 2px"
            if is_empty
            else ""
        )

        if self.panel_save_button is not None:
            self.panel_save_button.setDisabled(is_empty)

    def build_tag(self) -> Tag:
        color = self.color_field.currentData() or TagColor.DEFAULT

        tag = self.tag

        self.add_aliases()

        tag.name = self.name_field.text()
        tag.shorthand = self.shorthand_field.text()
        tag.color = color

        logger.info("built tag", tag=tag)
        return tag
