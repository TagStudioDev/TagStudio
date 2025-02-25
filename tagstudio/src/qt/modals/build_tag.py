# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import sys
from typing import cast

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library, Tag
from src.core.library.alchemy.enums import TagColorEnum
from src.core.library.alchemy.models import TagColorGroup
from src.core.palette import ColorType, UiColor, get_tag_color, get_ui_color
from src.qt.modals.tag_color_selection import TagColorSelection
from src.qt.modals.tag_search import TagSearchPanel
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelModal, PanelWidget
from src.qt.widgets.tag import (
    TagWidget,
    get_border_color,
    get_highlight_color,
    get_primary_color,
    get_text_color,
)
from src.qt.widgets.tag_color_preview import TagColorPreview

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
        self.tag: Tag  # NOTE: This gets set at the end of the init.
        self.tag_color_namespace: str | None
        self.tag_color_slug: str | None
        self.disambiguation_id: int | None

        self.setMinimumSize(300, 460)
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
        self.name_title = QLabel(Translations["tag.name"])
        self.name_layout.addWidget(self.name_title)
        self.name_field = QLineEdit()
        self.name_field.setFixedHeight(24)
        self.name_field.textChanged.connect(self.on_name_changed)
        self.name_field.setPlaceholderText(Translations["tag.tag_name_required"])
        self.name_layout.addWidget(self.name_field)

        # Shorthand ------------------------------------------------------------
        self.shorthand_widget = QWidget()
        self.shorthand_layout = QVBoxLayout(self.shorthand_widget)
        self.shorthand_layout.setStretch(1, 1)
        self.shorthand_layout.setContentsMargins(0, 0, 0, 0)
        self.shorthand_layout.setSpacing(0)
        self.shorthand_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.shorthand_title = QLabel(Translations["tag.shorthand"])
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
        self.aliases_title = QLabel(Translations["tag.aliases"])
        self.aliases_layout.addWidget(self.aliases_title)

        self.aliases_table = QTableWidget(0, 2)
        self.aliases_table.horizontalHeader().setVisible(False)
        self.aliases_table.verticalHeader().setVisible(False)
        self.aliases_table.horizontalHeader().setStretchLastSection(True)
        self.aliases_table.setColumnWidth(0, 32)
        self.aliases_table.setTabKeyNavigation(False)
        self.aliases_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.aliases_add_button = QPushButton()
        self.aliases_add_button.setText("+")
        self.aliases_add_button.clicked.connect(self.add_alias_callback)

        # Parent Tags ----------------------------------------------------------
        self.parent_tags_widget = QWidget()
        self.parent_tags_widget.setMinimumHeight(128)
        self.parent_tags_layout = QVBoxLayout(self.parent_tags_widget)
        self.parent_tags_layout.setStretch(1, 1)
        self.parent_tags_layout.setContentsMargins(0, 0, 0, 0)
        self.parent_tags_layout.setSpacing(0)
        self.parent_tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.disam_button_group = QButtonGroup(self)
        self.disam_button_group.setExclusive(False)

        self.parent_tags_title = QLabel(Translations["tag.parent_tags"])
        self.parent_tags_layout.addWidget(self.parent_tags_title)

        self.scroll_contents = QWidget()
        self.parent_tags_scroll_layout = QVBoxLayout(self.scroll_contents)
        self.parent_tags_scroll_layout.setContentsMargins(6, 6, 6, 0)
        self.parent_tags_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.scroll_contents)
        self.parent_tags_layout.addWidget(self.scroll_area)

        self.parent_tags_add_button = QPushButton()
        self.parent_tags_add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.parent_tags_add_button.setText("+")
        self.parent_tags_layout.addWidget(self.parent_tags_add_button)

        exclude_ids: list[int] = list()
        if tag is not None:
            exclude_ids.append(tag.id)

        tsp = TagSearchPanel(self.lib, exclude_ids)
        tsp.tag_chosen.connect(lambda x: self.add_parent_tag_callback(x))
        self.add_tag_modal = PanelModal(tsp)
        self.add_tag_modal.setTitle(Translations["tag.parent_tags.add"])
        self.add_tag_modal.setWindowTitle(Translations["tag.parent_tags.add"])
        self.parent_tags_add_button.clicked.connect(self.add_tag_modal.show)

        # Color ----------------------------------------------------------------
        self.color_widget = QWidget()
        self.color_layout = QVBoxLayout(self.color_widget)
        self.color_layout.setStretch(1, 1)
        self.color_layout.setContentsMargins(0, 0, 0, 6)
        self.color_layout.setSpacing(6)
        self.color_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.color_title = QLabel(Translations["tag.color"])
        self.color_layout.addWidget(self.color_title)
        self.color_button: TagColorPreview
        try:
            self.color_button = TagColorPreview(self.lib, tag.color)
        except Exception as e:
            # TODO: Investigate why this happens during tests
            logger.error("[BuildTag] Could not access Tag member attributes", error=e)
            self.color_button = TagColorPreview(self.lib, None)
        self.tag_color_selection = TagColorSelection(self.lib)
        chose_tag_color_title = Translations["tag.choose_color"]
        self.choose_color_modal = PanelModal(
            self.tag_color_selection,
            chose_tag_color_title,
            chose_tag_color_title,
            done_callback=lambda: self.choose_color_callback(
                self.tag_color_selection.selected_color
            ),
        )
        self.color_button.button.clicked.connect(self.choose_color_modal.show)
        self.color_layout.addWidget(self.color_button)

        # Category -------------------------------------------------------------
        self.cat_widget = QWidget()
        self.cat_layout = QHBoxLayout(self.cat_widget)
        self.cat_layout.setStretch(1, 1)
        self.cat_layout.setContentsMargins(0, 0, 0, 0)
        self.cat_layout.setSpacing(6)
        self.cat_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.cat_title = QLabel(Translations["tag.is_category"])
        self.cat_checkbox = QCheckBox()
        self.cat_checkbox.setFixedSize(22, 22)

        primary_color = QColor(get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT))
        border_color = get_border_color(primary_color)
        highlight_color = get_highlight_color(primary_color)
        text_color: QColor = get_text_color(primary_color, highlight_color)

        self.cat_checkbox.setStyleSheet(
            f"QCheckBox{{"
            f"background: rgba{primary_color.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"border-color: rgba{border_color.toTuple()};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"}}"
            f"QCheckBox::indicator{{"
            f"width: 10px;"
            f"height: 10px;"
            f"border-radius: 2px;"
            f"margin: 4px;"
            f"}}"
            f"QCheckBox::indicator:checked{{"
            f"background: rgba{text_color.toTuple()};"
            f"}}"
            f"QCheckBox::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
            f"QCheckBox::focus{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"outline:none;"
            f"}}"
        )
        self.cat_layout.addWidget(self.cat_checkbox)
        self.cat_layout.addWidget(self.cat_title)

        # Add Widgets to Layout ================================================
        self.root_layout.addWidget(self.name_widget)
        self.root_layout.addWidget(self.shorthand_widget)
        self.root_layout.addWidget(self.aliases_widget)
        self.root_layout.addWidget(self.aliases_table)
        self.root_layout.addWidget(self.aliases_add_button)
        self.root_layout.addWidget(self.parent_tags_widget)
        self.root_layout.addWidget(self.color_widget)
        self.root_layout.addWidget(QLabel("<h3>Properties</h3>"))
        self.root_layout.addWidget(self.cat_widget)

        self.parent_ids: set[int] = set()
        self.alias_ids: list[int] = []
        self.alias_names: list[str] = []
        self.new_alias_names: dict = {}
        self.new_item_id = sys.maxsize

        self.set_tag(tag or Tag(name=Translations["tag.new"]))

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

    def add_parent_tag_callback(self, tag_id: int):
        logger.info("add_parent_tag_callback", tag_id=tag_id)
        self.parent_ids.add(tag_id)
        self.set_parent_tags()

    def remove_parent_tag_callback(self, tag_id: int):
        logger.info("remove_parent_tag_callback", tag_id=tag_id)
        self.parent_ids.remove(tag_id)
        self.set_parent_tags()

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

    def choose_color_callback(self, tag_color_group: TagColorGroup | None):
        logger.info("choose_color_callback", tag_color_group=tag_color_group)
        if tag_color_group:
            self.tag_color_namespace = tag_color_group.namespace
            self.tag_color_slug = tag_color_group.slug
        else:
            self.tag_color_namespace = None
            self.tag_color_slug = None
        self.color_button.set_tag_color_group(tag_color_group)

    def set_parent_tags(self):
        while self.parent_tags_scroll_layout.itemAt(0):
            self.parent_tags_scroll_layout.takeAt(0).widget().deleteLater()

        c = QWidget()
        layout = QVBoxLayout(c)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        last_tab: QWidget = self.aliases_table.cellWidget(self.aliases_table.rowCount() - 1, 1)
        next_tab: QWidget = last_tab

        for parent_id in self.parent_ids:
            tag = self.lib.get_tag(parent_id)
            if not tag:
                continue
            is_disam = parent_id == self.disambiguation_id
            last_tab, next_tab, container = self.__build_row_item_widget(tag, parent_id, is_disam)
            layout.addWidget(container)
            # TODO: Disam buttons after the first currently can't be added due to this error:
            # QWidget::setTabOrder: 'first' and 'second' must be in the same window
            self.setTabOrder(last_tab, next_tab)

        self.setTabOrder(next_tab, self.name_field)
        self.parent_tags_scroll_layout.addWidget(c)

    def __build_row_item_widget(self, tag: Tag, parent_id: int, is_disambiguation: bool):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)

        # Init Colors
        primary_color = get_primary_color(tag)
        border_color = (
            get_border_color(primary_color)
            if not (tag.color and tag.color.secondary and tag.color.color_border)
            else (QColor(tag.color.secondary))
        )
        highlight_color = get_highlight_color(
            primary_color
            if not (tag.color and tag.color.secondary)
            else QColor(tag.color.secondary)
        )
        text_color: QColor
        if tag.color and tag.color.secondary:
            text_color = QColor(tag.color.secondary)
        else:
            text_color = get_text_color(primary_color, highlight_color)

        # Add Tag Widget
        tag_widget = TagWidget(
            tag,
            library=self.lib,
            has_edit=False,
            has_remove=True,
        )
        tag_widget.on_remove.connect(lambda t=parent_id: self.remove_parent_tag_callback(t))
        row.addWidget(tag_widget)

        # Add Disambiguation Tag Button
        disam_button = QRadioButton()
        disam_button.setObjectName(f"disambiguationButton.{parent_id}")
        disam_button.setFixedSize(22, 22)
        disam_button.setToolTip(Translations["tag.disambiguation.tooltip"])
        disam_button.setStyleSheet(
            f"QRadioButton{{"
            f"background: rgba{primary_color.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"border-color: rgba{border_color.toTuple()};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"}}"
            f"QRadioButton::indicator{{"
            f"width: 10px;"
            f"height: 10px;"
            f"border-radius: 2px;"
            f"margin: 4px;"
            f"}}"
            f"QRadioButton::indicator:checked{{"
            f"background: rgba{text_color.toTuple()};"
            f"}}"
            f"QRadioButton::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
            f"QRadioButton::pressed{{"
            f"background: rgba{border_color.toTuple()};"
            f"color: rgba{primary_color.toTuple()};"
            f"border-color: rgba{primary_color.toTuple()};"
            f"}}"
            f"QRadioButton::focus{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"outline:none;"
            f"}}"
        )

        self.disam_button_group.addButton(disam_button)
        if is_disambiguation:
            disam_button.setChecked(True)

        disam_button.clicked.connect(lambda checked=False: self.toggle_disam_id(parent_id))
        row.addWidget(disam_button)

        return tag_widget.bg_button, disam_button, container

    def toggle_disam_id(self, disambiguation_id: int | None):
        if self.disambiguation_id == disambiguation_id:
            self.disambiguation_id = None
        else:
            self.disambiguation_id = disambiguation_id

        for button in self.disam_button_group.buttons():
            if button.objectName() == f"disambiguationButton.{self.disambiguation_id}":
                button.setChecked(True)
            else:
                button.setChecked(False)

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
            elif name.strip() == "" and name in set(self.alias_names):
                self.alias_names.remove(name)

    def _update_new_alias_name_dict(self):
        for i in range(0, self.aliases_table.rowCount()):
            widget = self.aliases_table.cellWidget(i, 1)
            self.new_alias_names[widget.id] = widget.text()  # type: ignore

    def _set_aliases(self):
        self._update_new_alias_name_dict()

        while self.aliases_table.rowCount() > 0:
            self.aliases_table.removeRow(0)

        self.alias_names.clear()

        last: QWidget = self.panel_save_button
        for alias_id in self.alias_ids:
            alias = self.lib.get_alias(self.tag.id, alias_id)

            alias_name = alias.name if alias else self.new_alias_names[alias_id]

            # handel when an alias name changes
            if alias_id in self.new_alias_names:
                alias_name = self.new_alias_names[alias_id]

            self.alias_names.append(alias_name)

            remove_btn = QPushButton("-")
            remove_btn.clicked.connect(
                lambda a=alias_name, id=alias_id: self.remove_alias_callback(a, id)
            )

            row = self.aliases_table.rowCount()
            new_item = CustomTableItem(alias_name, self.enter, self.backspace)
            new_item.set_id(alias_id)

            new_item.editingFinished.connect(lambda item=new_item: self._alias_name_change(item))

            self.aliases_table.insertRow(row)
            self.aliases_table.setCellWidget(row, 1, new_item)
            self.aliases_table.setCellWidget(row, 0, remove_btn)

            self.setTabOrder(last, self.aliases_table.cellWidget(row, 1))
            self.setTabOrder(
                self.aliases_table.cellWidget(row, 1), self.aliases_table.cellWidget(row, 0)
            )
            last = self.aliases_table.cellWidget(row, 0)

    def _alias_name_change(self, item: CustomTableItem):
        self.new_alias_names[item.id] = item.text()

    def set_tag(self, tag: Tag):
        logger.info("[BuildTagPanel] Setting Tag", tag=tag)
        self.tag = tag

        self.name_field.setText(tag.name)
        self.shorthand_field.setText(tag.shorthand or "")

        for alias_id in tag.alias_ids:
            self.alias_ids.append(alias_id)
        self._set_aliases()

        self.disambiguation_id = tag.disambiguation_id
        for parent_id in tag.parent_ids:
            self.parent_ids.add(parent_id)
        self.set_parent_tags()

        try:
            self.tag_color_namespace = tag.color_namespace
            self.tag_color_slug = tag.color_slug
            self.color_button.set_tag_color_group(tag.color)
            self.tag_color_selection.select_radio_button(tag.color)
        except Exception as e:
            # TODO: Investigate why this happens during tests
            logger.error("[BuildTag] Could not access Tag member attributes", error=e)
            self.color_button.set_tag_color_group(None)

        self.cat_checkbox.setChecked(tag.is_category)

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
        tag = self.tag
        self.add_aliases()

        tag.name = self.name_field.text()
        tag.shorthand = self.shorthand_field.text()
        tag.disambiguation_id = self.disambiguation_id
        tag.color_namespace = self.tag_color_namespace
        tag.color_slug = self.tag_color_slug
        tag.is_category = self.cat_checkbox.isChecked()

        logger.info("built tag", tag=tag)
        return tag

    def parent_post_init(self):
        self.setTabOrder(self.name_field, self.shorthand_field)
        self.setTabOrder(self.shorthand_field, self.aliases_add_button)
        self.setTabOrder(self.aliases_add_button, self.parent_tags_add_button)
        self.setTabOrder(self.parent_tags_add_button, self.color_button)
        self.setTabOrder(self.color_button, self.panel_cancel_button)
        self.setTabOrder(self.panel_cancel_button, self.panel_save_button)
        self.setTabOrder(self.panel_save_button, self.aliases_table.cellWidget(0, 1))
        self.name_field.selectAll()
        self.name_field.setFocus()
