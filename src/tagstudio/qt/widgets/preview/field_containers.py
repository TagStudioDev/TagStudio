# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import sys
import typing
from collections.abc import Callable
from datetime import datetime as dt
from warnings import catch_warnings

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.enums import Theme
from tagstudio.core.library.alchemy.fields import (
    BaseField,
    DatetimeField,
    FieldTypeEnum,
    TextField,
)
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry, Tag
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.fields import FieldContainer
from tagstudio.qt.widgets.panel import PanelModal
from tagstudio.qt.widgets.tag_box import TagBoxWidget
from tagstudio.qt.widgets.text import TextWidget
from tagstudio.qt.widgets.text_box_edit import EditTextBox
from tagstudio.qt.widgets.text_line_edit import EditTextLine

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class FieldContainers(QWidget):
    """The Preview Panel Widget."""

    favorite_updated = Signal(bool)
    archived_updated = Signal(bool)

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()

        self.lib = library
        self.driver: QtDriver = driver
        self.initialized = False
        self.is_open: bool = False
        self.common_fields: list = []
        self.mixed_fields: list = []
        self.cached_entries: list[Entry] = []
        self.containers: list[FieldContainer] = []

        self.panel_bg_color = (
            Theme.COLOR_BG_DARK.value
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.COLOR_BG_LIGHT.value
        )

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(3, 3, 3, 3)
        self.scroll_layout.setSpacing(0)

        scroll_container: QWidget = QWidget()
        scroll_container.setObjectName("entryScrollContainer")
        scroll_container.setLayout(self.scroll_layout)

        info_section = QWidget()
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("entryScrollArea")
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # NOTE: I would rather have this style applied to the scroll_area
        # background and NOT the scroll container background, so that the
        # rounded corners are maintained when scrolling. I was unable to
        # find the right trick to only select that particular element.
        self.scroll_area.setStyleSheet(
            f"QWidget#entryScrollContainer{{background:{self.panel_bg_color};border-radius:6px;}}"
        )
        self.scroll_area.setWidget(scroll_container)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scroll_area)

    def update_from_entry(self, entry_id: int, update_badges: bool = True):
        """Update tags and fields from a single Entry source."""
        logger.warning("[FieldContainers] Updating Selection", entry_id=entry_id)

        self.cached_entries = [self.lib.get_entry_full(entry_id)]
        entry = self.cached_entries[0]
        self.update_granular(entry.tags, entry.fields, update_badges)

    def update_granular(
        self, entry_tags: set[Tag], entry_fields: list[BaseField], update_badges: bool = True
    ):
        """Individually update elements of the item preview."""
        container_len: int = len(entry_fields)
        container_index = 0
        # Write tag container(s)
        if entry_tags:
            categories = self.get_tag_categories(entry_tags)
            for cat, tags in sorted(categories.items(), key=lambda kv: (kv[0] is None, kv)):
                self.write_tag_container(
                    container_index, tags=tags, category_tag=cat, is_mixed=False
                )
                container_index += 1
                container_len += 1
        if update_badges:
            self.emit_badge_signals({t.id for t in entry_tags})

        # Write field container(s)
        for index, field in enumerate(entry_fields, start=container_index):
            self.write_container(index, field, is_mixed=False)

        # Hide leftover container(s)
        if len(self.containers) > container_len:
            for i, c in enumerate(self.containers):
                if i > (container_len - 1):
                    c.setHidden(True)

    def update_toggled_tag(self, tag_id: int, toggle_value: bool):
        """Visually add or remove a tag from the item preview without needing to query the db."""
        entry = self.cached_entries[0]
        tag = self.lib.get_tag(tag_id)
        if not tag:
            return
        new_tags = (
            entry.tags.union({tag}) if toggle_value else {t for t in entry.tags if t.id != tag_id}
        )
        self.update_granular(entry_tags=new_tags, entry_fields=entry.fields, update_badges=False)

    def hide_containers(self):
        """Hide all field and tag containers."""
        for c in self.containers:
            c.setHidden(True)

    def get_tag_categories(self, tags: set[Tag]) -> dict[Tag | None, set[Tag]]:
        """Get a dictionary of category tags mapped to their respective tags.
        Example:
        Tag: ["Johnny Bravo", Parent Tags: "Cartoon Network (TV)", "Character"] maps to:
        "Cartoon Network" -> Johnny Bravo,
        "Character" -> "Johnny Bravo",
        "TV" -> Johnny Bravo"
        """
        tag_parents, hierarchy_tags = self.lib.get_tag_hierarchy(t.id for t in tags)

        categories: dict[int | None, set[int]] = {None: set()}
        for tag in hierarchy_tags.values():
            if tag.is_category:
                categories[tag.id] = set()
        for tag in tags:
            has_category_parent = False
            parent_ids = tag_parents.get(tag.id, [])
            while len(parent_ids) > 0:
                grandparent_ids = set()
                for parent_id in parent_ids:
                    if parent_id in categories:
                        categories[parent_id].add(tag.id)
                        has_category_parent = True
                    grandparent_ids.update(tag_parents.get(parent_id, []))
                parent_ids = grandparent_ids
            if not has_category_parent:
                categories[None].add(tag.id)

        cats = {}
        for category_id, descendent_ids in categories.items():
            key = None if category_id is None else hierarchy_tags[category_id]
            cats[key] = {hierarchy_tags[d] for d in descendent_ids}
        logger.info("[FieldContainers] Tag Categories", categories=cats)
        return cats

    def remove_field_prompt(self, name: str) -> str:
        return Translations.format("library.field.confirm_remove", name=name)

    def add_field_to_selected(self, field_list: list):
        """Add list of entry fields to one or more selected items.

        Uses the current driver selection, NOT the field containers cache.
        """
        logger.info(
            "[FieldContainers][add_field_to_selected]",
            selected=self.driver.selected,
            fields=field_list,
        )
        for entry_id in self.driver.selected:
            for field_item in field_list:
                self.lib.add_field_to_entry(
                    entry_id,
                    field_id=field_item.data(Qt.ItemDataRole.UserRole),
                )

    def add_tags_to_selected(self, tags: int | list[int]):
        """Add list of tags to one or more selected items.

        Uses the current driver selection, NOT the field containers cache.
        """
        if isinstance(tags, int):
            tags = [tags]
        logger.info(
            "[FieldContainers][add_tags_to_selected]",
            selected=self.driver.selected,
            tags=tags,
        )
        for entry_id in self.driver.selected:
            self.lib.add_tags_to_entries(
                entry_id,
                tag_ids=tags,
            )
        self.emit_badge_signals(tags, emit_on_absent=False)

    def write_container(self, index: int, field: BaseField, is_mixed: bool = False):
        """Update/Create data for a FieldContainer.

        Args:
            index(int): The container index.
            field(BaseField): The type of field to write to.
            is_mixed(bool): Relevant when multiple items are selected.

            If True, field is not present in all selected items.
        """
        logger.info("[FieldContainers][write_field_container]", index=index)
        if len(self.containers) < (index + 1):
            container = FieldContainer()
            self.containers.append(container)
            self.scroll_layout.addWidget(container)
        else:
            container = self.containers[index]

        if field.type.type == FieldTypeEnum.TEXT_LINE:
            container.set_title(field.type.name)
            container.set_inline(False)

            # Normalize line endings in any text content.
            if not is_mixed:
                assert isinstance(field.value, (str, type(None)))
                text = field.value or ""
            else:
                text = "<i>Mixed Data</i>"

            title = f"{field.type.name} ({field.type.type.value})"
            inner_widget = TextWidget(title, text)
            container.set_inner_widget(inner_widget)
            if not is_mixed:
                modal = PanelModal(
                    EditTextLine(field.value),
                    title=title,
                    window_title=f"Edit {field.type.type.value}",
                    save_callback=(
                        lambda content: (
                            self.update_field(field, content),  # type: ignore
                            self.update_from_entry(self.cached_entries[0].id),
                        )
                    ),
                )
                if "pytest" in sys.modules:
                    # for better testability
                    container.modal = modal

                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.type.value),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_from_entry(self.cached_entries[0].id),
                        ),
                    )
                )

        elif field.type.type == FieldTypeEnum.TEXT_BOX:
            container.set_title(field.type.name)
            container.set_inline(False)
            # Normalize line endings in any text content.
            if not is_mixed:
                assert isinstance(field.value, (str, type(None)))
                text = (field.value or "").replace("\r", "\n")
            else:
                text = "<i>Mixed Data</i>"
            title = f"{field.type.name} (Text Box)"
            inner_widget = TextWidget(title, text)
            container.set_inner_widget(inner_widget)
            if not is_mixed:
                modal = PanelModal(
                    EditTextBox(field.value),
                    title=title,
                    window_title=f"Edit {field.type.name}",
                    save_callback=(
                        lambda content: (
                            self.update_field(field, content),  # type: ignore
                            self.update_from_entry(self.cached_entries[0].id),
                        )
                    ),
                )
                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.name),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_from_entry(self.cached_entries[0].id),
                        ),
                    )
                )

        elif field.type.type == FieldTypeEnum.DATETIME:
            if not is_mixed:
                try:
                    container.set_title(field.type.name)
                    container.set_inline(False)
                    # TODO: Localize this and/or add preferences.
                    date = dt.strptime(field.value, "%Y-%m-%d %H:%M:%S")
                    title = f"{field.type.name} (Date)"
                    inner_widget = TextWidget(title, date.strftime("%D - %r"))
                    container.set_inner_widget(inner_widget)
                except Exception:
                    container.set_title(field.type.name)
                    container.set_inline(False)
                    title = f"{field.type.name} (Date) (Unknown Format)"
                    inner_widget = TextWidget(title, str(field.value))
                    container.set_inner_widget(inner_widget)

                container.set_edit_callback()
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.name),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_from_entry(self.cached_entries[0].id),
                        ),
                    )
                )
            else:
                text = "<i>Mixed Data</i>"
                title = f"{field.type.name} (Wacky Date)"
                inner_widget = TextWidget(title, text)
                container.set_inner_widget(inner_widget)
        else:
            logger.warning("[FieldContainers][write_container] Unknown Field", field=field)
            container.set_title(field.type.name)
            container.set_inline(False)
            title = f"{field.type.name} (Unknown Field Type)"
            inner_widget = TextWidget(title, field.type.name)
            container.set_inner_widget(inner_widget)
            container.set_remove_callback(
                lambda: self.remove_message_box(
                    prompt=self.remove_field_prompt(field.type.name),
                    callback=lambda: (
                        self.remove_field(field),
                        self.update_from_entry(self.cached_entries[0].id),
                    ),
                )
            )

        container.setHidden(False)

    def write_tag_container(
        self, index: int, tags: set[Tag], category_tag: Tag | None = None, is_mixed: bool = False
    ):
        """Update/Create tag data for a FieldContainer.

        Args:
            index(int): The container index.
            tags(set[Tag]): The list of tags for this container.
            category_tag(Tag|None): The category tag this container represents.
            is_mixed(bool): Relevant when multiple items are selected.

            If True, field is not present in all selected items.
        """
        logger.info("[FieldContainers][write_tag_container]", index=index)
        if len(self.containers) < (index + 1):
            container = FieldContainer()
            self.containers.append(container)
            self.scroll_layout.addWidget(container)
        else:
            container = self.containers[index]

        container.set_title("Tags" if not category_tag else category_tag.name)
        container.set_inline(False)

        if not is_mixed:
            inner_widget = container.get_inner_widget()

            if isinstance(inner_widget, TagBoxWidget):
                inner_widget.set_tags(tags)
                with catch_warnings(record=True):
                    inner_widget.updated.disconnect()

            else:
                inner_widget = TagBoxWidget(
                    tags,
                    "Tags",
                    self.driver,
                )
                container.set_inner_widget(inner_widget)

            inner_widget.updated.connect(
                lambda: (self.update_from_entry(self.cached_entries[0].id, update_badges=True))
            )
        else:
            text = "<i>Mixed Data</i>"
            inner_widget = TextWidget("Mixed Tags", text)
            container.set_inner_widget(inner_widget)

        container.set_edit_callback()
        container.set_remove_callback()
        container.setHidden(False)

    def remove_field(self, field: BaseField):
        """Remove a field from all selected Entries."""
        logger.info(
            "[FieldContainers] Removing Field",
            field=field,
            selected=[x.path for x in self.cached_entries],
        )
        entry_ids = [e.id for e in self.cached_entries]
        self.lib.remove_entry_field(field, entry_ids)

    def update_field(self, field: BaseField, content: str) -> None:
        """Update a field in all selected Entries, given a field object."""
        assert isinstance(
            field,
            (TextField, DatetimeField),
        ), f"instance: {type(field)}"

        entry_ids = [e.id for e in self.cached_entries]

        assert entry_ids, "No entries selected"
        self.lib.update_entry_field(
            entry_ids,
            field,
            content,
        )

    def remove_message_box(self, prompt: str, callback: Callable) -> None:
        remove_mb = QMessageBox()
        remove_mb.setText(prompt)
        remove_mb.setWindowTitle("Remove Field")
        remove_mb.setIcon(QMessageBox.Icon.Warning)
        cancel_button = remove_mb.addButton(
            Translations["generic.cancel_alt"], QMessageBox.ButtonRole.DestructiveRole
        )
        remove_mb.addButton("&Remove", QMessageBox.ButtonRole.RejectRole)
        remove_mb.setEscapeButton(cancel_button)
        result = remove_mb.exec_()
        if result == QMessageBox.ButtonRole.ActionRole.value:
            callback()

    def emit_badge_signals(self, tag_ids: list[int] | set[int], emit_on_absent: bool = True):
        """Emit any connected signals for updating badge icons."""
        logger.info("[emit_badge_signals] Emitting", tag_ids=tag_ids, emit_on_absent=emit_on_absent)
        if TAG_ARCHIVED in tag_ids:
            self.archived_updated.emit(True)  # noqa: FBT003
        elif emit_on_absent:
            self.archived_updated.emit(False)  # noqa: FBT003

        if TAG_FAVORITE in tag_ids:
            self.favorite_updated.emit(True)  # noqa: FBT003
        elif emit_on_absent:
            self.favorite_updated.emit(False)  # noqa: FBT003
