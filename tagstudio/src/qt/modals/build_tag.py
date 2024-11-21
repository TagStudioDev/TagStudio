# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
from typing import cast

import structlog
from PySide6 import QtCore
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QAction,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library, Tag
from src.core.library.alchemy.enums import TagColor
from src.core.palette import ColorType, UiColor, get_tag_color, get_ui_color
from src.qt.flowlayout import FlowLayout
from src.qt.modals.tag_search import TagSearchPanel
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import TagAliasWidget, TagWidget

logger = structlog.get_logger(__name__)


class BuildTagPanel(PanelWidget):
    on_edit = Signal(Tag)

    def __init__(self, library: Library, tag: Tag | None = None):
        super().__init__()
        self.lib = library
        # self.callback = callback
        # self.tag_id = tag_id

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

        self.aliases_flow_widget = QWidget()
        self.aliases_flow_layout = FlowLayout(self.aliases_flow_widget)
        self.aliases_flow_layout.setContentsMargins(0, 0, 0, 0)
        self.aliases_flow_layout.enable_grid_optimizations(value=False)

        self.alias_add_button = QPushButton()
        self.alias_add_button.setMinimumSize(23, 23)
        self.alias_add_button.setMaximumSize(23, 23)
        self.alias_add_button.setText("+")
        self.alias_add_button.setToolTip("CTRL + A")
        self.alias_add_button.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_A,
            )
        )
        self.alias_add_button.setStyleSheet(
            f"QPushButton{{"
            f"background: #1e1e1e;"
            f"color: #FFFFFF;"
            f"font-weight: bold;"
            f"border-color: #333333;"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width:{math.ceil(self.devicePixelRatio())}px;"
            f"padding-bottom: 5px;"
            f"font-size: 20px;"
            f"}}"
            f"QPushButton::hover"
            f"{{"
            f"border-color: #CCCCCC;"
            f"background: #555555;"
            f"}}"
        )

        self.alias_add_button.clicked.connect(lambda: self.add_alias_callback())
        self.aliases_flow_layout.addWidget(self.alias_add_button)

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

        self.subtag_flow_widget = QWidget()
        self.subtag_flow_layout = FlowLayout(self.subtag_flow_widget)
        self.subtag_flow_layout.setContentsMargins(0, 0, 0, 0)
        self.subtag_flow_layout.enable_grid_optimizations(value=False)

        self.subtags_add_button = QPushButton()
        self.subtags_add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.subtags_add_button.setText("+")
        self.subtags_add_button.setToolTip("CTRL + P")
        self.subtags_add_button.setMinimumSize(23, 23)
        self.subtags_add_button.setMaximumSize(23, 23)
        self.subtags_add_button.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_P,
            )
        )
        self.subtags_add_button.setStyleSheet(
            f"QPushButton{{"
            f"background: #1e1e1e;"
            f"color: #FFFFFF;"
            f"font-weight: bold;"
            f"border-color: #333333;"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width:{math.ceil(self.devicePixelRatio())}px;"
            f"padding-bottom: 5px;"
            f"font-size: 20px;"
            f"}}"
            f"QPushButton::hover"
            f"{{"
            f"border-color: #CCCCCC;"
            f"background: #555555;"
            f"}}"
        )
        self.subtag_flow_layout.addWidget(self.subtags_add_button)

        exclude_ids: list[int] = list()
        if tag is not None:
            exclude_ids.append(tag.id)

        tsp = TagSearchPanel(self.lib, exclude_ids)
        tsp.tag_chosen.connect(lambda x: self.add_subtag_callback(x))
        self.add_tag_modal = PanelModal(tsp, "Add Parent Tags", "Add Parent Tags")
        self.subtags_add_button.clicked.connect(self.add_tag_modal.show)
        # self.subtags_layout.addWidget(self.subtags_add_button)

        # self.subtags_field = TagBoxWidget()
        # self.subtags_field.setMinimumHeight(60)
        # self.subtags_layout.addWidget(self.subtags_field)

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
        remove_selected_alias_action = QAction("remove selected alias", self)
        remove_selected_alias_action.triggered.connect(self.remove_selected_alias)
        remove_selected_alias_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_D,
            )
        )
        self.addAction(remove_selected_alias_action)

        # Add Widgets to Layout ================================================
        self.root_layout.addWidget(self.name_widget)
        self.root_layout.addWidget(self.shorthand_widget)
        self.root_layout.addWidget(self.aliases_widget)
        self.root_layout.addWidget(self.aliases_flow_widget)
        self.root_layout.addWidget(self.subtags_widget)
        self.root_layout.addWidget(self.subtag_flow_widget)
        self.root_layout.addWidget(self.color_widget)
        # self.parent().done.connect(self.update_tag)

        self.subtag_ids: set[int] = set()
        self.alias_ids: set[int] = set()
        self.alias_names: set[str] = set()
        self.new_alias_names: dict = dict()

        self.set_tag(tag or Tag(name="New Tag"))
        if tag is None:
            self.name_field.selectAll()

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:  # type: ignore
            focused_widget = QApplication.focusWidget()
            if isinstance(focused_widget.parent(), TagAliasWidget):
                self.add_alias_callback()

    def remove_selected_alias(self):
        count = self.aliases_flow_layout.count()
        if count <= 0:
            return

        focused_widget = QApplication.focusWidget()

        if focused_widget is None:
            return

        if isinstance(focused_widget.parent(), TagAliasWidget):
            cast(TagAliasWidget, focused_widget.parent()).on_remove.emit()

        count = self.aliases_flow_layout.count()
        if count > 1:
            cast(
                TagAliasWidget, self.aliases_flow_layout.itemAt(count - 2).widget()
            ).text_field.setFocus()
        else:
            self.alias_add_button.setFocus()

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
        # bug passing in the text for a here means when the text changes
        # the remove callback uses what a whas initialy assigned
        new_field = TagAliasWidget()
        id = new_field.__hash__()
        new_field.id = id

        new_field.on_remove.connect(lambda a="": self.remove_alias_callback(a, id))
        new_field.setMaximumHeight(25)
        new_field.setMinimumHeight(25)

        self.alias_ids.add(id)
        self.new_alias_names[id] = ""
        self.aliases_flow_layout.addWidget(new_field)
        new_field.text_field.setFocus()
        self.aliases_flow_layout.addWidget(self.alias_add_button)

    def remove_alias_callback(self, alias_name: str, alias_id: int | None = None):
        logger.info("remove_alias_callback")
        self.alias_ids.remove(alias_id)
        self._set_aliases()

    def set_subtags(self):
        while self.subtag_flow_layout.itemAt(1):
            self.subtag_flow_layout.takeAt(0).widget().deleteLater()

        for tag_id in self.subtag_ids:
            tag = self.lib.get_tag(tag_id)
            tw = TagWidget(tag, has_edit=False, has_remove=True)
            tw.on_remove.connect(lambda t=tag_id: self.remove_subtag_callback(t))
            self.subtag_flow_layout.addWidget(tw)

        self.subtag_flow_layout.addWidget(self.subtags_add_button)

    def add_aliases(self):
        fields: set[TagAliasWidget] = set()
        for i in range(0, self.aliases_flow_layout.count() - 1):
            widget = self.aliases_flow_layout.itemAt(i).widget()

            if not isinstance(widget, TagAliasWidget):
                return

            field: TagAliasWidget = cast(TagAliasWidget, widget)
            fields.add(field)

        remove: set[str] = self.alias_names - set([a.text_field.text() for a in fields])

        self.alias_names = self.alias_names - remove

        for field in fields:
            # add new aliases
            if field.text_field.text() != "":
                self.alias_names.add(field.text_field.text())

    def _update_new_alias_name_dict(self):
        for i in range(0, self.aliases_flow_layout.count() - 1):
            widget = self.aliases_flow_layout.itemAt(i).widget()

            if not isinstance(widget, TagAliasWidget):
                return

            field: TagAliasWidget = cast(TagAliasWidget, widget)
            text_field_text = field.text_field.text()

            self.new_alias_names[field.id] = text_field_text

    def _set_aliases(self):
        self._update_new_alias_name_dict()

        while self.aliases_flow_layout.itemAt(1):
            self.aliases_flow_layout.takeAt(0).widget().deleteLater()

        self.alias_names.clear()

        for alias_id in self.alias_ids:
            alias = self.lib.get_alias(self.tag.id, alias_id)

            alias_name = alias.name if alias else self.new_alias_names[alias_id]

            new_field = TagAliasWidget(
                alias_id,
                alias_name,
                lambda a=alias_name, id=alias_id: self.remove_alias_callback(a, id),
            )
            new_field.setMaximumHeight(25)
            new_field.setMinimumHeight(25)
            self.aliases_flow_layout.addWidget(new_field)
            self.alias_names.add(alias_name)

        self.aliases_flow_layout.addWidget(self.alias_add_button)

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
