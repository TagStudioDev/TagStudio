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
from tagstudio.qt.widgets.datetime_picker import DatetimePicker
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

        entry = self.lib.get_entry_full(entry_id)
        assert entry is not None
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
        """Get a dictionary of category tags mapped to their respective tags."""
        cats: dict[Tag | None, set[Tag]] = {}
        cats[None] = set()

        base_tag_ids: set[int] = {x.id for x in tags}
        exhausted: set[int] = set()
        cluster_map: dict[int, set[int]] = {}

        def add_to_cluster(tag_id: int, p_ids: list[int] | None = None):
            """Maps a Tag's child tags' IDs back to it's parent tag's ID.

            Example:
            Tag: ["Johnny Bravo", Parent Tags: "Cartoon Network (TV)", "Character"] maps to:
            "Cartoon Network" -> Johnny Bravo,
            "Character" -> "Johnny Bravo",
            "TV" -> Johnny Bravo"
            """
            tag_obj = self.lib.get_tag(tag_id)  # Get full object
            if p_ids is None:
                assert tag_obj is not None
                p_ids = tag_obj.parent_ids

            for p_id in p_ids:
                if cluster_map.get(p_id) is None:
                    cluster_map[p_id] = set()
                # If the p_tag has p_tags of its own, recursively link those to the original Tag.
                if tag_id not in cluster_map[p_id]:
                    cluster_map[p_id].add(tag_id)
                    p_tag = self.lib.get_tag(p_id)  # Get full object
                    assert p_tag is not None
                    if p_tag.parent_ids:
                        add_to_cluster(
                            tag_id,
                            [sub_id for sub_id in p_tag.parent_ids if sub_id != tag_id],
                        )
                exhausted.add(p_id)
            exhausted.add(tag_id)

        for tag in tags:
            add_to_cluster(tag.id)

        logger.info("[FieldContainers] Entry Cluster", entry_cluster=exhausted)
        logger.info("[FieldContainers] Cluster Map", cluster_map=cluster_map)

        # Initialize all categories from parents.
        tags_ = {t for tid in exhausted if (t := self.lib.get_tag(tid)) is not None}
        for tag in tags_:
            if tag.is_category:
                cats[tag] = set()
        logger.info("[FieldContainers] Blank Tag Categories", cats=cats)

        # Add tags to any applicable categories.
        added_ids: set[int] = set()
        for key in cats:
            logger.info("[FieldContainers] Checking category tag key", key=key)

            if key:
                logger.info(
                    "[FieldContainers] Key cluster:", key=key, cluster=cluster_map.get(key.id)
                )

                if final_tags := cluster_map.get(key.id, set()).union([key.id]):
                    cats[key] = {
                        t
                        for tid in final_tags
                        if tid in base_tag_ids and (t := self.lib.get_tag(tid)) is not None
                    }
                    added_ids = added_ids.union({tid for tid in final_tags if tid in base_tag_ids})

        # Add remaining tags to None key (general case).
        cats[None] = {
            t
            for tid in base_tag_ids
            if tid not in added_ids and (t := self.lib.get_tag(tid)) is not None
        }
        logger.info(
            "[FieldContainers] Key cluster: None, general case!",
            general_tags=cats[None],
            added=added_ids,
            base_tag_ids=base_tag_ids,
        )

        # Remove unused categories
        empty: list[Tag | None] = []
        for k, v in list(cats.items()):
            if not v:
                empty.append(k)
        for key in empty:
            cats.pop(key, None)

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
