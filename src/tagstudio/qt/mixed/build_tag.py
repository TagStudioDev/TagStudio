# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from functools import partial
from typing import cast, override

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent
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

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag, TagAlias, TagColorGroup
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.controllers.tag_search_panel_controller import TagSearchPanel
from tagstudio.qt.mixed.tag_color_preview import TagColorPreview
from tagstudio.qt.mixed.tag_color_selection import TagColorSelection
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.search_panel_view import SearchPanelView
from tagstudio.qt.views.stylesheets.stylesheets import (
    checkbox_style,
    colored_radio_button_style,
    get_tag_border_color,
    get_tag_highlight_color,
    get_tag_primary_color,
    get_tag_text_color,
    header,
    line_edit_style,
)

logger = structlog.get_logger(__name__)


class CustomTableItem(QLineEdit):
    # TODO: Look into using signals instead of callbacks
    def __init__(
        self,
        text: str,
        on_return: Callable[..., None],
        on_backspace: Callable[..., None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setText(text)
        self.on_return: Callable[..., None] = on_return
        self.on_backspace: Callable[..., None] = on_backspace
        self.alias: TagAlias

    @override
    def keyPressEvent(self, arg__1: QKeyEvent):
        if arg__1.key() == Qt.Key.Key_Return or arg__1.key() == Qt.Key.Key_Enter:
            self.on_return()
        elif arg__1.key() == Qt.Key.Key_Backspace and self.text().strip() == "":
            self.on_backspace()
        else:
            super().keyPressEvent(arg__1)


class BuildTagPanel(ModalContent):
    on_edit = Signal(Tag)

    def __init__(self, library: Library, tag: Tag | None = None) -> None:
        super().__init__()
        self._lib = library
        self.tag: Tag  # NOTE: This gets set at the end of the init.
        self.tag_color_namespace: str | None
        self.tag_color_slug: str | None
        self.disambiguation_id: int | None
        self.parent_ids: set[int] = set()
        self.aliases: list[TagAlias] = []

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
        self.name_field.textChanged.connect(self._on_name_change)
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
        self.aliases_add_button.clicked.connect(self._create_alias_callback)

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

        tsp_view = SearchPanelView(placeholder_text=Translations["home.search_tags"])
        tsp = TagSearchPanel(self._lib, exclude=exclude_ids, view=tsp_view)
        self.add_tag_modal = Modal(tsp, title=Translations["tag.add.plural"])
        tsp.item_chosen.connect(lambda x: self._add_parent_tag_callback(x))

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
            assert tag is not None
            self.color_button = TagColorPreview(self._lib, tag.color)
        except Exception as e:
            # TODO: Investigate why this happens during tests
            logger.error("[BuildTag] Could not access Tag member attributes", error=e)
            self.color_button = TagColorPreview(self._lib, None)
        self.tag_color_selection = TagColorSelection(self._lib)
        chose_tag_color_title = Translations["tag.choose_color"]
        self.choose_color_modal = Modal(
            self.tag_color_selection, chose_tag_color_title, chose_tag_color_title
        )
        self.choose_color_modal.done.connect(
            lambda: self.choose_color_callback(self.tag_color_selection.selected_color)
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
        self.cat_checkbox.setStyleSheet(checkbox_style())
        self.cat_layout.addWidget(self.cat_checkbox)
        self.cat_layout.addWidget(self.cat_title)

        # Hidden ---------------------------------------------------------------
        self.hidden_widget = QWidget()
        self.hidden_layout = QHBoxLayout(self.hidden_widget)
        self.hidden_layout.setStretch(1, 1)
        self.hidden_layout.setContentsMargins(0, 0, 0, 0)
        self.hidden_layout.setSpacing(6)
        self.hidden_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.hidden_title = QLabel(Translations["tag.is_hidden"])
        self.hidden_checkbox = QCheckBox()
        self.hidden_checkbox.setFixedSize(22, 22)
        self.hidden_checkbox.setStyleSheet(checkbox_style())
        self.hidden_layout.addWidget(self.hidden_checkbox)
        self.hidden_layout.addWidget(self.hidden_title)

        # Add Widgets to Layout ================================================
        self.root_layout.addWidget(self.name_widget)
        self.root_layout.addWidget(self.shorthand_widget)
        self.root_layout.addWidget(self.aliases_widget)
        self.root_layout.addWidget(self.aliases_table)
        self.root_layout.addWidget(self.aliases_add_button)
        self.root_layout.addWidget(self.parent_tags_widget)
        self.root_layout.addWidget(self.color_widget)
        self.root_layout.addWidget(QLabel(header(Translations["tag.properties"], 3)))
        self.root_layout.addWidget(self.cat_widget)
        self.root_layout.addWidget(self.hidden_widget)

        self.set_tag(tag or Tag(name=Translations["tag.new"]))

    def backspace(self):
        focused_widget = QApplication.focusWidget()
        row = self.aliases_table.rowCount()

        if isinstance(focused_widget, CustomTableItem) is False:
            return
        remove_row = 0
        for i in range(0, row):
            item = self.aliases_table.cellWidget(i, 1)
            if isinstance(item, CustomTableItem) and item == cast(CustomTableItem, focused_widget):
                cast(QPushButton, self.aliases_table.cellWidget(i, 0)).click()
                remove_row = i
                break

        if self.aliases_table.rowCount() <= 0:
            return

        if remove_row == 0:
            remove_row = 1

        self.aliases_table.cellWidget(remove_row - 1, 1).setFocus()

    def enter(self):
        """When the Enter/Return key has been pressed."""
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, CustomTableItem):
            self._create_alias_callback()

    def _add_parent_tag_callback(self, tag_id: int):
        self.parent_ids.add(tag_id)
        self.set_parent_tags()

    def _remove_parent_tag_callback(self, tag_id: int):
        self.parent_ids.remove(tag_id)
        self.set_parent_tags()

    def _create_alias_callback(self):
        alias = TagAlias("", tag_id=self.tag.id)
        self.aliases.append(alias)

        self._set_aliases()
        row = self.aliases_table.rowCount() - 1
        item = self.aliases_table.cellWidget(row, 1)
        item.setFocus()

    def remove_alias_callback(self, alias: TagAlias):
        for i, a in enumerate(self.aliases):
            if a.name == alias.name and a.id == alias.id:
                del self.aliases[i]
                continue
        self._set_aliases()

    def choose_color_callback(self, tag_color_group: TagColorGroup | None):
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
            tag = self._lib.get_tag(parent_id)
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
        primary_color = get_tag_primary_color(tag)
        border_color = (
            get_tag_border_color(primary_color)
            if not (tag.color and tag.color.secondary and tag.color.color_border)
            else (QColor(tag.color.secondary))
        )
        highlight_color = get_tag_highlight_color(
            primary_color
            if not (tag.color and tag.color.secondary)
            else QColor(tag.color.secondary)
        )
        text_color: QColor
        if tag.color and tag.color.secondary:
            text_color = QColor(tag.color.secondary)
        else:
            text_color = get_tag_text_color(primary_color, highlight_color)

        def update_parent_tag_callback(build_tag_panel: BuildTagPanel):
            self._lib.update_tag(
                build_tag_panel.build_tag(),
                parent_ids=set(build_tag_panel.parent_ids),
                aliases=set(build_tag_panel.aliases),
            )
            self.set_parent_tags()

        def on_parent_tag_edit(tag: Tag) -> None:
            build_tag_panel = BuildTagPanel(self._lib, tag=tag)
            edit_modal = Modal(
                build_tag_panel,
                self._lib.tag_display_name(tag),
                "Edit Tag",
                is_savable=True,
            )
            edit_modal.saved.connect(partial(update_parent_tag_callback, build_tag_panel))
            edit_modal.show()

        # Add Tag Widget
        tag_widget = TagWidget(tag, library=self._lib, has_edit=True, has_remove=True)
        tag_widget.on_remove.connect(lambda t=parent_id: self._remove_parent_tag_callback(t))
        tag_widget.on_edit.connect(partial(on_parent_tag_edit, tag))

        row.addWidget(tag_widget)

        # Add Disambiguation Tag Button
        disam_button = QRadioButton()
        disam_button.setObjectName(f"disambiguationButton.{parent_id}")
        disam_button.setFixedSize(22, 22)
        disam_button.setToolTip(Translations["tag.disambiguation.tooltip"])
        disam_button.setStyleSheet(
            colored_radio_button_style(primary_color, text_color, border_color, highlight_color)
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

    def _set_aliases(self):
        while self.aliases_table.rowCount() > 0:
            self.aliases_table.removeRow(0)

        last: QWidget | None = self.save_button
        aliases = list(self.aliases)
        alias_names = [a.name for a in aliases]
        sorted_aliases = sorted(aliases, key=lambda x: alias_names[aliases.index(x)])

        # Sort the TagAlias objects while keeping in-progress empty ones at the bottom
        empty_aliases: list[TagAlias] = []
        while sorted_aliases and sorted_aliases[0].name == "":
            empty_aliases.append(sorted_aliases.pop(0))
        for alias in empty_aliases:
            sorted_aliases.append(alias)

        for alias in sorted_aliases:
            remove_button = QPushButton("-")
            remove_button.clicked.connect(partial(self.remove_alias_callback, alias))

            row = self.aliases_table.rowCount()
            new_item = CustomTableItem(alias.name, self.enter, self.backspace)
            new_item.alias = alias
            new_item.editingFinished.connect(partial(self._on_alias_change, new_item))

            self.aliases_table.insertRow(row)
            self.aliases_table.setCellWidget(row, 1, new_item)
            self.aliases_table.setCellWidget(row, 0, remove_button)

            if last is not None:
                self.setTabOrder(last, self.aliases_table.cellWidget(row, 1))
            self.setTabOrder(
                self.aliases_table.cellWidget(row, 1), self.aliases_table.cellWidget(row, 0)
            )
            last = self.aliases_table.cellWidget(row, 0)

    def _on_alias_change(self, item: CustomTableItem):
        for alias in self.aliases:
            if item.alias == alias:
                alias.name = item.text()
                item.alias.name = item.text()
                continue

    def set_tag(self, tag: Tag):
        logger.info("[BuildTagPanel] Setting Tag", tag_id=tag.id)
        self.tag = tag
        self.name_field.setText(tag.name)
        self.shorthand_field.setText(tag.shorthand or "")

        for alias in tag.aliases:
            self.aliases.append(alias)
        self._set_aliases()

        self.disambiguation_id = tag.disambiguation_id
        for parent_id in self.tag.parent_ids:
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
        self.hidden_checkbox.setChecked(tag.is_hidden)

    def _on_name_change(self):
        is_empty = not self.name_field.text().strip()
        self.name_field.setStyleSheet(line_edit_style() if is_empty else "")

        if self.save_button is not None:
            self.save_button.setDisabled(is_empty)

    def build_tag(self) -> Tag:
        tag = self.tag
        tag.name = self.name_field.text()
        tag.shorthand = self.shorthand_field.text()
        tag.disambiguation_id = self.disambiguation_id
        tag.color_namespace = self.tag_color_namespace
        tag.color_slug = self.tag_color_slug
        tag.is_category = self.cat_checkbox.isChecked()
        tag.is_hidden = self.hidden_checkbox.isChecked()

        logger.info("[BuildTag] Build Tag", tag_id=tag.id, tag_name=tag.name)
        return tag

    @override
    def parent_post_init(self):
        self.setTabOrder(self.name_field, self.shorthand_field)
        self.setTabOrder(self.shorthand_field, self.aliases_add_button)
        self.setTabOrder(self.aliases_add_button, self.parent_tags_add_button)
        self.setTabOrder(self.parent_tags_add_button, self.color_button)
        self.setTabOrder(self.color_button, unwrap(self.cancel_button))
        self.setTabOrder(unwrap(self.cancel_button), unwrap(self.save_button))
        self.setTabOrder(unwrap(self.save_button), self.aliases_table.cellWidget(0, 1))
        self.name_field.selectAll()
        self.name_field.setFocus()
