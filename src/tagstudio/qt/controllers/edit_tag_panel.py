# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from functools import partial
from typing import cast, override

import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag, TagAlias, TagColorGroup
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers import tag_search_panel  # Module import due to circular import
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.mixed.tag_color_selection import TagColorSelection
from tagstudio.qt.views.edit_tag_panel_view import EditTagPanelView
from tagstudio.qt.views.search_panel_view import SearchPanelView
from tagstudio.qt.views.styles.stylesheets import (
    colored_checkbox_style,
    colored_radio_button_style,
    line_edit_style,
    tag_colors,
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


class EditTagPanel(ModalContent):
    def __init__(self, library: Library, tag: Tag | None = None) -> None:
        super().__init__()
        self._lib = library
        self.tag: Tag  # NOTE: This gets set at the end of the init.
        self._color_namespace: str | None
        self._color_slug: str | None
        self._disambiguation_id: int | None
        self.parent_ids: set[int] = set()
        self.exclusion_ids: set[int] = set()
        self.aliases: list[TagAlias] = []

        self.setMinimumWidth(600)
        self.setLayout(EditTagPanelView())

        self._disam_button_group = QButtonGroup(self)
        self._disam_button_group.setExclusive(False)

        tsp_view = SearchPanelView(placeholder_text=Translations["home.search_tags"])
        tsp = tag_search_panel.TagSearchPanel(
            self._lib, exclude=[tag.id] if tag else [], view=tsp_view
        )
        tsp.item_chosen.connect(self._add_parent_tag_callback)
        self._add_parent_tag_modal = Modal(tsp, title=Translations["tag.parent_tags.add"])

        self._color_selection = TagColorSelection(self._lib)
        choose_color_title = Translations["tag.choose_color"]
        self._choose_color_modal = Modal(
            self._color_selection, choose_color_title, choose_color_title
        )

        self._connect_callbacks()
        self.set_tag(tag or Tag(name=Translations["tag.new"]))

    @override
    def layout(self) -> EditTagPanelView:
        return super().layout()  # pyright: ignore[reportReturnType]

    def _connect_callbacks(self) -> None:
        view = self.layout()
        view.name_field.textChanged.connect(self._on_name_change)
        view.aliases_add_button.clicked.connect(self._create_alias_callback)
        view.parent_tags_add_button.clicked.connect(self._add_parent_tag_modal.show)
        view.color_button.on_click.connect(self._choose_color_modal.show)
        self._choose_color_modal.done.connect(
            lambda: self._choose_color_callback(self._color_selection.selected_color)
        )

    def _backspace(self):
        focused_widget = QApplication.focusWidget()
        aliases_table = self.layout().aliases_table
        row = aliases_table.rowCount()

        if isinstance(focused_widget, CustomTableItem) is False:
            return
        remove_row = 0
        for i in range(0, row):
            item = aliases_table.cellWidget(i, 1)
            if isinstance(item, CustomTableItem) and item == cast(CustomTableItem, focused_widget):
                cast(QPushButton, aliases_table.cellWidget(i, 0)).click()
                remove_row = i
                break

        if aliases_table.rowCount() <= 0:
            return

        if remove_row == 0:
            remove_row = 1

        aliases_table.cellWidget(remove_row - 1, 1).setFocus()

    def _enter(self):
        """When the Enter/Return key has been pressed."""
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, CustomTableItem):
            self._create_alias_callback()

    def _add_parent_tag_callback(self, tag_id: int):
        self.parent_ids.add(tag_id)
        self._set_parent_tags()
        self._set_categories(added_parent_id=tag_id)

    def _remove_parent_tag_callback(self, tag_id: int):
        self.parent_ids.remove(tag_id)
        self._set_parent_tags()
        self._set_categories(removed_parent=True)

    def _create_alias_callback(self):
        alias = TagAlias("", tag_id=self.tag.id)
        self.aliases.append(alias)

        self._set_aliases()
        aliases_table = self.layout().aliases_table
        aliases_table.cellWidget(aliases_table.rowCount() - 1, 1).setFocus()

    def _remove_alias_callback(self, alias: TagAlias):
        for i, a in enumerate(self.aliases):
            if a.name == alias.name and a.id == alias.id:
                del self.aliases[i]
                continue
        self._set_aliases()

    def _choose_color_callback(self, tag_color_group: TagColorGroup | None):
        if tag_color_group:
            self._color_namespace = tag_color_group.namespace
            self._color_slug = tag_color_group.slug
        else:
            self._color_namespace = None
            self._color_slug = None
        self._set_color_button(tag_color_group)

    def _set_color_button(self, color_group: TagColorGroup | None) -> None:
        color_button = self.layout().color_button
        color_button.set_color_group(color_group)
        color_button.set_text(
            f"{color_group.name} ({self._lib.get_namespace_name(color_group.namespace)})"
            if color_group
            else Translations["color.title.no_color"]
        )

    def _edit_tag(self, tag: Tag, on_saved: Callable[[], None]) -> None:
        """Open a nested modal to edit another tag, such as a parent or category."""
        panel = EditTagPanel(self._lib, tag=tag)
        edit_modal = Modal(
            panel,
            self._lib.tag_display_name(tag),
            Translations["tag.edit"],
            is_savable=True,
        )

        def update_tag():
            self._lib.update_tag(
                panel.build_tag(),
                parent_ids=set(panel.parent_ids),
                aliases=set(panel.aliases),
                exclusion_ids=set(panel.exclusion_ids),
            )
            on_saved()

        edit_modal.saved.connect(update_tag)
        edit_modal.show()

    def _set_categories(self, added_parent_id: int | None = None, removed_parent: bool = False):
        category_scroll_layout = self.layout().category_scroll_layout
        while category_scroll_layout.itemAt(0):
            category_scroll_layout.takeAt(0).widget().deleteLater()  # pyright: ignore[reportOptionalMemberAccess]

        c = QWidget()
        layout = QVBoxLayout(c)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        if removed_parent:
            tags_by_category: dict[Tag, set[Tag]] = {}
            hierarchy = set(self._lib.get_tag_hierarchy(self.parent_ids).values())
            for tag in hierarchy:
                if tag.is_category:
                    tags_by_category[tag] = set()
            for tag in hierarchy:
                for parent in self._lib.get_tag_hierarchy([tag.id]).values():
                    if parent in tags_by_category:
                        if tag == parent and parent.id not in self.parent_ids:
                            continue
                        tags_by_category[parent].add(tag)

            for category, tags in tags_by_category.items():
                if len(tags) == 0:
                    continue

                last_tab, next_tab, container = self._build_category_row_widget(category)
                layout.addWidget(container)
                self.setTabOrder(last_tab, next_tab)
        else:
            tag_ids = set(self.parent_ids)
            if added_parent_id is not None:
                tag_ids.add(added_parent_id)

            for tag in self._lib.get_tag_hierarchy(tag_ids).values():
                if not tag.is_category or tag == self.tag:
                    continue
                last_tab, next_tab, container = self._build_category_row_widget(tag)
                layout.addWidget(container)
                self.setTabOrder(last_tab, next_tab)
        category_scroll_layout.addWidget(c)

    def _build_category_row_widget(self, category: Tag) -> tuple[QPushButton, QCheckBox, QWidget]:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)

        def update_category_exclusion(category_tag: Tag, checked: bool) -> None:
            if checked:
                self.exclusion_ids.remove(category_tag.id)
            else:
                self.exclusion_ids.add(category_tag.id)

        # Add Tag Capsule
        capsule = Capsule(has_edit=True)
        capsule.set_text(self._lib.tag_display_name(category))
        capsule.set_color_group(category.color)
        capsule.on_edit.connect(partial(self._edit_tag, category, self._set_categories))
        row.addWidget(capsule)

        # Add Category Exclusion Tag Button
        include_checkbox = QCheckBox()
        include_checkbox.setFixedSize(22, 22)
        include_checkbox.setToolTip(Translations["tag.categories.tooltip"])
        include_checkbox.setStyleSheet(colored_checkbox_style(*tag_colors(category.color)))

        if category.id not in self.exclusion_ids:
            include_checkbox.setChecked(True)
        include_checkbox.toggled.connect(partial(update_category_exclusion, category))

        row.addWidget(include_checkbox)

        return capsule.layout().button, include_checkbox, container

    def _set_parent_tags(self):
        view = self.layout()
        while view.parent_tags_scroll_layout.itemAt(0):
            view.parent_tags_scroll_layout.takeAt(0).widget().deleteLater()  # pyright: ignore[reportOptionalMemberAccess]

        c = QWidget()
        layout = QVBoxLayout(c)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        last_tab: QWidget = view.aliases_table.cellWidget(view.aliases_table.rowCount() - 1, 1)
        next_tab: QWidget = last_tab

        for parent_id in self.parent_ids:
            tag = self._lib.get_tag(parent_id)
            if not tag:
                continue
            is_disam = parent_id == self._disambiguation_id
            last_tab, next_tab, container = self._build_parent_row_widget(tag, parent_id, is_disam)
            layout.addWidget(container)
            # TODO: Disam buttons after the first currently can't be added due to this error:
            # QWidget::setTabOrder: 'first' and 'second' must be in the same window
            self.setTabOrder(last_tab, next_tab)

        self.setTabOrder(next_tab, view.name_field)
        view.parent_tags_scroll_layout.addWidget(c)

    def _build_parent_row_widget(self, tag: Tag, parent_id: int, is_disambiguation: bool):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)

        # Add Tag Capsule
        capsule = Capsule(has_edit=True, has_remove=True)
        capsule.set_text(self._lib.tag_display_name(tag))
        capsule.set_color_group(tag.color)
        capsule.on_remove.connect(lambda t=parent_id: self._remove_parent_tag_callback(t))
        capsule.on_edit.connect(partial(self._edit_tag, tag, self._set_parent_tags))

        row.addWidget(capsule)

        # Add Disambiguation Tag Button
        disam_button = QRadioButton()
        disam_button.setObjectName(f"disambiguationButton.{parent_id}")
        disam_button.setFixedSize(22, 22)
        disam_button.setToolTip(Translations["tag.disambiguation.tooltip"])
        disam_button.setStyleSheet(colored_radio_button_style(*tag_colors(tag.color)))

        self._disam_button_group.addButton(disam_button)
        if is_disambiguation:
            disam_button.setChecked(True)

        disam_button.clicked.connect(lambda checked=False: self._toggle_disam_id(parent_id))
        row.addWidget(disam_button)

        return capsule.layout().button, disam_button, container

    def _toggle_disam_id(self, disambiguation_id: int | None):
        if self._disambiguation_id == disambiguation_id:
            self._disambiguation_id = None
        else:
            self._disambiguation_id = disambiguation_id

        for button in self._disam_button_group.buttons():
            if button.objectName() == f"disambiguationButton.{self._disambiguation_id}":
                button.setChecked(True)
            else:
                button.setChecked(False)

    def _set_aliases(self):
        aliases_table = self.layout().aliases_table
        while aliases_table.rowCount() > 0:
            aliases_table.removeRow(0)

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
            remove_button.clicked.connect(partial(self._remove_alias_callback, alias))

            row = aliases_table.rowCount()
            new_item = CustomTableItem(alias.name, self._enter, self._backspace)
            new_item.alias = alias
            new_item.editingFinished.connect(partial(self._on_alias_change, new_item))

            aliases_table.insertRow(row)
            aliases_table.setCellWidget(row, 1, new_item)
            aliases_table.setCellWidget(row, 0, remove_button)

            if last is not None:
                self.setTabOrder(last, aliases_table.cellWidget(row, 1))
            self.setTabOrder(aliases_table.cellWidget(row, 1), aliases_table.cellWidget(row, 0))
            last = aliases_table.cellWidget(row, 0)

    def _on_alias_change(self, item: CustomTableItem):
        for alias in self.aliases:
            if item.alias == alias:
                alias.name = item.text()
                item.alias.name = item.text()
                continue

    def set_tag(self, tag: Tag):
        logger.info("[EditTagPanel] Setting Tag", tag_id=tag.id)
        view = self.layout()
        self.tag = tag
        view.name_field.setText(tag.name)
        view.shorthand_field.setText(tag.shorthand or "")

        for alias in tag.aliases:
            self.aliases.append(alias)
        self._set_aliases()

        self._disambiguation_id = tag.disambiguation_id
        for parent_id in self.tag.parent_ids:
            self.parent_ids.add(parent_id)
        self._set_parent_tags()

        for exclusion_id in tag.exclusion_ids:
            self.exclusion_ids.add(exclusion_id)
        self._set_categories()

        try:
            self._color_namespace = tag.color_namespace
            self._color_slug = tag.color_slug
            self._set_color_button(tag.color)
            self._color_selection.select_radio_button(tag.color)
        except Exception as e:
            # TODO: Investigate why this happens during tests
            logger.error("[EditTagPanel] Could not access Tag member attributes", error=e)
            self._set_color_button(None)

        view.is_category_checkbox.setChecked(tag.is_category)
        view.is_hidden_checkbox.setChecked(tag.is_hidden)

    def set_name(self, name: str):
        self.layout().name_field.setText(name)

    def _on_name_change(self):
        name_field = self.layout().name_field
        is_empty = not name_field.text().strip()
        name_field.setStyleSheet(line_edit_style() if is_empty else "")

        if self.save_button is not None:
            self.save_button.setDisabled(is_empty)

    def build_tag(self) -> Tag:
        view = self.layout()
        tag = self.tag
        tag.name = view.name_field.text()
        tag.shorthand = view.shorthand_field.text()
        tag.disambiguation_id = self._disambiguation_id
        tag.color_namespace = self._color_namespace
        tag.color_slug = self._color_slug
        tag.is_category = view.is_category_checkbox.isChecked()
        tag.is_hidden = view.is_hidden_checkbox.isChecked()

        logger.info("[EditTagPanel] Build Tag", tag_id=tag.id, tag_name=tag.name)
        return tag

    @override
    def parent_post_init(self):
        view = self.layout()
        self.setTabOrder(view.name_field, view.shorthand_field)
        self.setTabOrder(view.shorthand_field, view.aliases_add_button)
        self.setTabOrder(view.aliases_add_button, view.parent_tags_add_button)
        self.setTabOrder(view.parent_tags_add_button, view.color_button)
        self.setTabOrder(view.color_button, unwrap(self.cancel_button))
        self.setTabOrder(unwrap(self.cancel_button), unwrap(self.save_button))
        self.setTabOrder(unwrap(self.save_button), view.aliases_table.cellWidget(0, 1))
        view.name_field.selectAll()
        view.name_field.setFocus()
