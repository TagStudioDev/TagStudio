# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from collections.abc import Callable
from datetime import datetime as dt
from functools import partial
from warnings import catch_warnings

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.library.alchemy.fields import (
    BaseField,
    BaseFieldTemplate,
    DatetimeField,
    TextField,
)
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry, Tag
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.edit_text_controller import EditText
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.tag_box_controller import TagBoxWidget
from tagstudio.qt.mixed.datetime_picker import DatetimePicker
from tagstudio.qt.mixed.field_widget import FieldContainer
from tagstudio.qt.mixed.text_field import TextContainerWidget
from tagstudio.qt.translations import FIELD_TYPE_KEYS, Translations
from tagstudio.qt.views.stylesheets.stylesheets import inset_container_style

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class FieldContainers(QWidget):
    """Widget for the tag and field containers displayed inside the Preview Panel."""

    on_tags_update = Signal()

    def __init__(self, library: Library, driver: "QtDriver") -> None:
        super().__init__()

        self.lib = library
        self.driver: QtDriver = driver
        self.initialized = False
        self.is_open: bool = False
        self.common_fields: list = []
        self.mixed_fields: list = []
        self.cached_entries: list[Entry] = []
        self._containers: list[FieldContainer] = []

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(3, 3, 3, 3)
        self.scroll_layout.setSpacing(6)

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
        self.scroll_area.setStyleSheet(inset_container_style("entryScrollContainer"))
        self.scroll_area.setWidget(scroll_container)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scroll_area)

    @property
    def top_entry_id(self) -> int:
        """Get the topmost entry ID in the (cached) selected entries."""
        return self.cached_entries[0].id

    def update_from_entry(self, entry_id: int, update_badges: bool = True) -> None:
        """Update tags and fields from a single Entry source."""
        logger.warning("[FieldContainers] Updating Selection", entry_id=entry_id)

        entry = unwrap(self.lib.get_entry_full(entry_id))
        self.cached_entries = [entry]
        self.update_granular(entry.tags, entry.fields, update_badges)

    def update_granular(
        self, entry_tags: set[Tag], entry_fields: list[BaseField], update_badges: bool = True
    ) -> None:
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
            self.write_field_container(index, field, is_mixed=False)

        # Hide leftover container(s)
        if len(self._containers) > container_len:
            for i, c in enumerate(self._containers):
                if i > (container_len - 1):
                    c.setHidden(True)

    def update_toggled_tag(self, tag_id: int, toggle_value: bool) -> None:
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

    def hide_containers(self) -> None:
        """Hide all field and tag containers."""
        for c in self._containers:
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
        return Translations.format("field.confirm_remove", name=name)

    def add_field_to_selected(
        self, field_templates: BaseFieldTemplate | list[BaseFieldTemplate]
    ) -> None:
        """Add list of fields to one or more selected items.

        Uses the current driver selection, NOT the field containers cache.
        """
        if isinstance(field_templates, BaseFieldTemplate):
            field_templates = [field_templates]

        assert isinstance(field_templates, list)

        logger.info(
            "[FieldContainers][add_field_to_selected]",
            selected=self.driver.selected,
            fields=[
                (field_template.class_name, field_template.id) for field_template in field_templates
            ],
        )

        for entry_id in self.driver.selected:
            for field_template in field_templates:
                logger.info(
                    "[FieldContainers][add_field_to_selected] Adding field",
                    name=field_template.name,
                    type=field_template.class_name,
                )
                self.lib.add_field_to_entries(entry_id, field_template.to_field())

    def add_tags_to_selected(self, tag_ids: int | list[int]) -> None:
        """Add list of tags to one or more selected items.

        Uses the current driver selection, NOT the field containers cache.
        """
        if isinstance(tag_ids, int):
            tag_ids = [tag_ids]
        logger.info(
            "[FieldContainers][add_tags_to_selected]",
            selected=self.driver.selected,
            tag_ids=tag_ids,
        )
        self.driver.add_tags_to_selected_callback(tag_ids)

    def update_text_field_callback(
        self, field: TextField, entry_id: int, content: dict[str, str | bool]
    ) -> None:
        """Callback called when a text field has updated data."""
        self._update_text_field(
            field, str(content["name"]), str(content["value"]), bool(content["is_multiline"])
        )
        self.update_from_entry(entry_id)

    def update_datetime_field_callback(
        self, field: DatetimeField, entry_id: int, content: dict[str, str]
    ) -> None:
        """Callback called when a datetime field has updated data."""
        self.update_datetime_field(field, str(content["name"]), str(content["value"]))
        self.update_from_entry(entry_id)

    def remove_field_callback(self, field: BaseField, entry_id: int) -> None:
        """Callback called when a field needs to be removed from an entry."""
        self._remove_field(field)
        self.update_from_entry(entry_id)

    def write_field_container(self, index: int, field: BaseField, is_mixed: bool = False) -> None:
        """Update/Create data for a field FieldContainer.

        Args:
            index(int): The container index.
            field(BaseField): The field to write in this container.
            is_mixed(bool): Relevant when multiple items are selected.
                If True, field is not present in all selected items.
        """

        def write_text_container(
            container: FieldContainer, field: TextField, title: str, is_mixed: bool
        ):
            container.set_title(field.name)

            # Normalize line endings in any text content.
            if not is_mixed:
                assert isinstance(field.value, str | type(None))
                text = (field.value or "").replace("\r", "\n")
            else:
                text = f"<i>{Translations['field.mixed_data']}</i>"

            inner_widget = TextContainerWidget(title, text)
            container.set_inner_widget(inner_widget)

            if not is_mixed:
                edit_modal = Modal(
                    EditText(field.name, field.value, field.is_multiline),
                    window_title=f"{Translations['field.edit']} ({Translations[field_name_key]})",
                    is_savable=True,
                    inline_title=False,
                )
                edit_modal.saved_data.connect(
                    partial(self.update_text_field_callback, field, self.top_entry_id)
                )

                container.set_edit_callback(edit_modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(title),
                        callback=partial(self.remove_field_callback, field, self.top_entry_id),
                    )
                )

        def write_datetime_container(
            container: FieldContainer, field: DatetimeField, title: str, is_mixed: bool
        ):
            container.set_title(field.name)

            if not is_mixed:
                try:
                    assert field.value is not None
                    text = self.driver.settings.format_datetime(
                        DatetimePicker.string2dt(field.value)
                    )
                except (ValueError, AssertionError):
                    text = str(field.value)
            else:
                text = f"<i>{Translations['field.mixed_data']}</i>"

            inner_widget = TextContainerWidget(title, text)
            container.set_inner_widget(inner_widget)

            if not is_mixed:
                edit_modal = Modal(
                    DatetimePicker(self.driver, field.name, field.value or dt.now()),
                    window_title=f"{Translations['field.edit']} ({Translations[field_name_key]})",
                    is_savable=True,
                    inline_title=False,
                )
                edit_modal.saved_data.connect(
                    partial(self.update_datetime_field_callback, field, self.top_entry_id)
                )

                container.set_edit_callback(edit_modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.name),
                        callback=partial(self.remove_field_callback, field, self.top_entry_id),
                    )
                )

        def write_unknown_container():
            container.set_title(field.name)
            inner_widget = TextContainerWidget(title, field.name)
            container.set_inner_widget(inner_widget)
            container.set_remove_callback(
                lambda: self.remove_message_box(
                    prompt=self.remove_field_prompt(field.name),
                    callback=partial(self.remove_field_callback, field, self.top_entry_id),
                )
            )

        logger.info(
            "[FieldContainers][write_container]",
            index=index,
            name=field.name,
            type=field.class_name,
        )

        # Create new containers if necessary
        if len(self._containers) < (index + 1):
            container = FieldContainer()
            self._containers.append(container)
            self.scroll_layout.addWidget(container)
        else:
            container = self._containers[index]

        # Set field title
        field_name_key: str = FIELD_TYPE_KEYS.get(field.class_name, "field_type.unknown")
        title = f"{field.name} ({Translations[field_name_key]})"

        # Write containers
        if type(field) is TextField:
            write_text_container(container, field, title, is_mixed)
        elif type(field) is DatetimeField:
            write_datetime_container(container, field, title, is_mixed)
        else:
            write_unknown_container()

        container.setHidden(False)

    def write_tag_container(
        self, index: int, tags: set[Tag], category_tag: Tag | None = None, is_mixed: bool = False
    ) -> None:
        """Update/Create tag data for a tag FieldContainer.

        Args:
            index(int): The container index.
            tags(set[Tag]): The list of tags for this container.
            category_tag(Tag|None): The category tag this container represents.
            is_mixed(bool): Relevant when multiple items are selected.
                If True, field is not present in all selected items.
        """
        logger.info("[FieldContainers][write_tag_container]", index=index)
        if len(self._containers) < (index + 1):
            container = FieldContainer()
            self._containers.append(container)
            self.scroll_layout.addWidget(container)
        else:
            container = self._containers[index]

        container.set_title(Translations["entries.tags"] if not category_tag else category_tag.name)

        if not is_mixed:
            inner_widget = container.get_inner_widget()

            if isinstance(inner_widget, TagBoxWidget):
                with catch_warnings(record=True):
                    inner_widget.on_update.disconnect()

            else:
                inner_widget = TagBoxWidget(Translations["entries.tags"], self.driver)
                container.set_inner_widget(inner_widget)
            inner_widget.set_entries([e.id for e in self.cached_entries])
            inner_widget.set_tags(tags)

            inner_widget.on_update.connect(
                lambda: (
                    self.update_from_entry(self.cached_entries[0].id, update_badges=True),
                    self.on_tags_update.emit(),
                )
            )
        else:
            text = f"<i>{Translations['field.mixed_data']}</i>"
            inner_widget = TextContainerWidget("Mixed Tags", text)  # NOTE: Unlocalized but unused
            container.set_inner_widget(inner_widget)

        container.set_edit_callback()
        container.set_remove_callback()
        container.setHidden(False)

    def _remove_field(self, field: BaseField) -> None:
        """Remove a field from all selected Entries."""
        logger.info(
            "[FieldContainers] Removing Field",
            field=field,
            selected=[x.path for x in self.cached_entries],
        )
        entry_ids = [e.id for e in self.cached_entries]
        self.lib.remove_entry_field(field, entry_ids)

    def _update_text_field(
        self, field: TextField, name: str, value: str, is_multiline: bool
    ) -> None:
        """Update a text field across selected entries."""
        entry_ids = [e.id for e in self.cached_entries]
        assert entry_ids, "No entries selected"

        self.lib.update_text_field(entry_ids, field, name, value, is_multiline)

    def update_datetime_field(self, field: DatetimeField, name: str, value: str) -> None:
        """Update a datetime field across selected entries."""
        entry_ids = [e.id for e in self.cached_entries]
        assert entry_ids, "No entries selected"

        self.lib.update_datetime_field(entry_ids, field, name, dt.fromisoformat(value))

    def remove_message_box(self, prompt: str, callback: Callable[..., None]) -> None:
        remove_mb = QMessageBox()
        remove_mb.setText(prompt)
        remove_mb.setWindowTitle(Translations["Remove Field"])
        remove_mb.setIcon(QMessageBox.Icon.Warning)
        cancel_button = remove_mb.addButton(
            Translations["generic.cancel_alt"], QMessageBox.ButtonRole.DestructiveRole
        )
        remove_mb.addButton("&Remove", QMessageBox.ButtonRole.RejectRole)
        remove_mb.setEscapeButton(cancel_button)
        result = remove_mb.exec_()
        if result == QMessageBox.ButtonRole.ActionRole.value:
            callback()

    @property
    def tags(self) -> list[int]:
        if len(self.cached_entries) <= 0:
            return []
        entry = self.cached_entries[0]
        entry_ = self.lib.get_entry_full(entry.id, with_fields=False)
        if not entry_:
            return []
        return [tag.id for tag in entry_.tags]
