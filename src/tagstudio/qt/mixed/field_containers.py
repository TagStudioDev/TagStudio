# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import sys
import typing
from collections.abc import Callable
from datetime import datetime as dt
from warnings import catch_warnings

import structlog
from PySide6.QtCore import Qt
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

from tagstudio.core.enums import Theme
from tagstudio.core.library.alchemy.enums import FieldTypeEnum
from tagstudio.core.library.alchemy.fields import (
    BaseField,
    DatetimeField,
    TextField,
)
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry, Tag
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.tag_box_controller import TagBoxWidget
from tagstudio.qt.mixed.datetime_picker import DatetimePicker
from tagstudio.qt.mixed.field_widget import FieldContainer
from tagstudio.qt.mixed.text_field import TextWidget
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.edit_text_box_modal import EditTextBox
from tagstudio.qt.views.edit_text_line_modal import EditTextLine
from tagstudio.qt.views.panel_modal import PanelModal

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class FieldContainers(QWidget):
    """The Preview Panel Widget."""

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

        entry = unwrap(self.lib.get_entry_full(entry_id))
        self.cached_entries = [entry]
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
            self.driver.emit_badge_signals({t.id for t in entry_tags})

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
        if toggle_value:
            entry.tags.add(tag)
        else:
            entry.tags.discard(tag)

        self.update_granular(entry_tags=entry.tags, entry_fields=entry.fields, update_badges=False)

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
        loop_cutoff = 1024  # Used for stopping the while loop

        hierarchy_tags = self.lib.get_tag_hierarchy(t.id for t in tags)
        categories: dict[Tag | None, set[Tag]] = {None: set()}

        for tag in hierarchy_tags.values():
            if tag.is_category:
                categories[tag] = set()
        for tag in tags:
            tag = hierarchy_tags[tag.id]
            has_category_parent = False
            parent_tags = tag.parent_tags

            loop_counter = 0
            while len(parent_tags) > 0:
                # NOTE: This is for preventing infinite loops in the event a tag is parented
                # to itself cyclically.
                loop_counter += 1
                if loop_counter >= loop_cutoff:
                    break

                grandparent_tags: set[Tag] = set()
                for parent_tag in parent_tags:
                    if parent_tag in categories:
                        categories[parent_tag].add(tag)
                        has_category_parent = True
                    grandparent_tags.update(parent_tag.parent_tags)
                parent_tags = grandparent_tags

            if tag.is_category:
                categories[tag].add(tag)
            elif not has_category_parent:
                categories[None].add(tag)

        return dict((c, d) for c, d in categories.items() if len(d) > 0)

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
        self.lib.add_tags_to_entries(
            self.driver.selected,
            tag_ids=tags,
        )
        self.driver.emit_badge_signals(tags, emit_on_absent=False)

        group_by_tag_id = self.driver.browsing_history.current.group_by_tag_id
        if group_by_tag_id is not None:
            relevant_tag_ids = self.lib.get_grouping_tag_ids(group_by_tag_id)
            if any(tag_id in relevant_tag_ids for tag_id in tags):
                self.driver.update_browsing_state()

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
                assert isinstance(field.value, str | type(None))
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
                    container.modal = modal  # pyright: ignore[reportAttributeAccessIssue]

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
                assert isinstance(field.value, str | type(None))
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
            logger.info("[FieldContainers][write_container] Datetime Field", field=field)
            if not is_mixed:
                container.set_title(field.type.name)
                container.set_inline(False)

                title = f"{field.type.name} (Date)"
                try:
                    assert field.value is not None
                    text = self.driver.settings.format_datetime(
                        DatetimePicker.string2dt(field.value)
                    )
                except (ValueError, AssertionError):
                    title += " (Unknown Format)"
                    text = str(field.value)

                inner_widget = TextWidget(title, text)
                container.set_inner_widget(inner_widget)

                modal = PanelModal(
                    DatetimePicker(self.driver, field.value or dt.now()),
                    title=f"Edit {field.type.name}",
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
                with catch_warnings(record=True):
                    inner_widget.on_update.disconnect()

            else:
                inner_widget = TagBoxWidget(
                    "Tags",
                    self.driver,
                )
                container.set_inner_widget(inner_widget)
            inner_widget.set_entries([e.id for e in self.cached_entries])
            inner_widget.set_tags(tags)

            inner_widget.on_update.connect(
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
            TextField | DatetimeField,
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
