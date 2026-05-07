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
from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
    QWidget,
)

from tagstudio.core.library.alchemy.enums import FieldTypeEnum
from tagstudio.core.library.alchemy.fields import (
    BaseField,
    DatetimeField,
    TextField,
)
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry, Tag
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.field_container_controller import FieldContainer
from tagstudio.qt.controllers.tag_box_controller import TagBoxWidget
from tagstudio.qt.mixed.datetime_picker import DatetimePicker
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.edit_text_box_modal import EditTextBox
from tagstudio.qt.views.edit_text_line_modal import EditTextLine
from tagstudio.qt.views.field_list_view import FieldListView
from tagstudio.qt.views.panel_modal import PanelModal
from tagstudio.qt.views.text_field_widget_view import TextFieldWidget

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


def remove_field_prompt(name: str) -> str:
    return Translations.format("library.field.confirm_remove", name=name)


class FieldListController(FieldListView):
    """A list of field containers."""

    def __init__(self, library: Library, driver: "QtDriver") -> None:
        super().__init__()

        self.__lib: Library = library
        self.__driver: QtDriver = driver

        self.__common_fields: list = []
        self.__mixed_fields: list = []
        self.__cached_entries: list[Entry] = []

    def update_from_entry(self, entry_id: int, update_badges: bool = True) -> None:
        """Update tags and fields from a single Entry source."""
        logger.warning("[FieldListController] Updating Selection", entry_id=entry_id)

        entry: Entry = unwrap(self.__lib.get_entry_full(entry_id))
        self.__cached_entries = [entry]
        self.update_granular(entry.tags, entry.fields, update_badges)

    def update_granular(
        self, entry_tags: set[Tag], entry_fields: list[BaseField], update_badges: bool = True
    ) -> None:
        """Individually update elements of the item preview."""
        num_containers: int = len(entry_fields)
        container_index: int = 0

        # Write tag container(s)
        if entry_tags:
            categories: dict[Tag | None, set[Tag]] = self.get_tag_categories(entry_tags)
            for category, tags in sorted(categories.items(), key=lambda kv: (kv[0] is None, kv)):
                self.write_tag_container(
                    container_index, tags=tags, category_tag=category, is_mixed=False
                )
                container_index += 1
                num_containers += 1

        if update_badges:
            self.__driver.emit_badge_signals({tag.id for tag in entry_tags})

        # Write field container(s)
        for index, field in enumerate(entry_fields, start=container_index):
            self.write_container(index, field, is_mixed=False)

        # Hide leftover container(s)
        self.hide_after(num_containers)

    def update_toggled_tag(self, tag_id: int, toggle_value: bool) -> None:
        """Visually toggle a tag from the item preview without needing to query the database."""
        entry: Entry = self.__cached_entries[0]
        tag: Tag | None = self.__lib.get_tag(tag_id)

        if not tag:
            return

        if toggle_value:
            entry.tags.add(tag)
        else:
            entry.tags.discard(tag)

        self.update_granular(entry_tags=entry.tags, entry_fields=entry.fields, update_badges=False)

    def get_tag_categories(self, tags: set[Tag]) -> dict[Tag | None, set[Tag]]:
        """Get a dictionary of category tags mapped to their respective tags.

        Example:
        Tag: ["Johnny Bravo", Parent Tags: "Cartoon Network (TV)", "Character"] maps to:
        "Cartoon Network" -> Johnny Bravo,
        "Character" -> "Johnny Bravo",
        "TV" -> Johnny Bravo"
        """
        loop_cutoff: int = 1024  # Used for stopping the while loop

        hierarchy_tags = self.__lib.get_tag_hierarchy(tag.id for tag in tags)
        categories: dict[Tag | None, set[Tag]] = {None: set()}

        for tag in hierarchy_tags.values():
            if tag.is_category:
                categories[tag] = set()

        for tag in tags:
            tag = hierarchy_tags[tag.id]
            has_category_parent: bool = False
            parent_tags: set[Tag] = tag.parent_tags

            loop_counter: int = 0
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

        return dict(
            (category, category_tags)
            for category, category_tags in categories.items()
            if len(category_tags) > 0
        )

    def add_field_to_selected(self, field_list: list) -> None:
        """Add list of entry fields to one or more selected items.

        Uses the current driver selection, NOT the field containers cache.
        """
        logger.info(
            "[FieldListController][add_field_to_selected]",
            selected=self.__driver.selected,
            fields=field_list,
        )
        for entry_id in self.__driver.selected:
            for field_item in field_list:
                self.__lib.add_field_to_entry(
                    entry_id,
                    field_id=field_item.data(Qt.ItemDataRole.UserRole),
                )

    def add_tags_to_selected(self, tags: int | list[int]) -> None:
        """Add list of tags to one or more selected items.

        Uses the current driver selection, NOT the field containers cache.
        """
        if isinstance(tags, int):
            tags = [tags]
            assert isinstance(tags, list)

        logger.info(
            "[FieldListController][add_tags_to_selected]",
            selected=self.__driver.selected,
            tags=tags,
        )

        self.__lib.add_tags_to_entries(
            self.__driver.selected,
            tag_ids=tags,
        )

        self.__driver.emit_badge_signals(tags, emit_on_absent=False)

    def write_container(self, index: int, field: BaseField, is_mixed: bool = False) -> None:
        """Update/Create data for a FieldContainer.

        Args:
            index(int): The container index.
            field(BaseField): The type of field to write to.
            is_mixed(bool): Relevant when multiple items are selected.

            If True, field is not present in all selected items.
        """
        logger.info("[FieldListController][write_field_container]", index=index)

        if len(self.field_containers) < (index + 1):
            container: FieldContainer = FieldContainer()
            self.field_containers.append(container)
            self.scroll_layout.addWidget(container)
        else:
            container = self.field_containers[index]

        if field.type.type == FieldTypeEnum.TEXT_LINE:
            container.set_title(field.type.name)
            container.set_inline(False)

            # Normalize line endings in any text content.
            if not is_mixed:
                assert isinstance(field.value, str | type(None))
                text: str = field.value if isinstance(field.value, str) else ""
            else:
                text = "<i>Mixed Data</i>"

            title: str = f"{field.type.name} ({field.type.type.value})"
            field_widget: TextFieldWidget = TextFieldWidget(title, text)
            container.set_field_widget(field_widget)
            if not is_mixed:
                modal: PanelModal = PanelModal(
                    EditTextLine(field.value),
                    title=title,
                    window_title=f"Edit {field.type.type.value}",
                    save_callback=(
                        lambda content: (
                            self.update_field(field, content),  # type: ignore
                            self.update_from_entry(self.__cached_entries[0].id),
                        )
                    ),
                )
                if "pytest" in sys.modules:
                    # for better testability
                    container.modal = modal  # pyright: ignore[reportAttributeAccessIssue]

                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=remove_field_prompt(field.type.type.value),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_from_entry(self.__cached_entries[0].id),
                        ),
                    )
                )

        elif field.type.type == FieldTypeEnum.TEXT_BOX:
            container.set_title(field.type.name)
            container.set_inline(False)
            # Normalize line endings in any text content.
            if not is_mixed:
                assert isinstance(field.value, str | type(None))
                text = (field.value if isinstance(field.value, str) else "").replace("\r", "\n")
            else:
                text = "<i>Mixed Data</i>"
            title = f"{field.type.name} (Text Box)"
            field_widget = TextFieldWidget(title, text)
            container.set_field_widget(field_widget)
            if not is_mixed:
                modal = PanelModal(
                    EditTextBox(field.value),
                    title=title,
                    window_title=f"Edit {field.type.name}",
                    save_callback=(
                        lambda content: (
                            self.update_field(field, content),  # type: ignore
                            self.update_from_entry(self.__cached_entries[0].id),
                        )
                    ),
                )
                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=remove_field_prompt(field.type.name),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_from_entry(self.__cached_entries[0].id),
                        ),
                    )
                )

        elif field.type.type == FieldTypeEnum.DATETIME:
            logger.info("[FieldListController][write_container] Datetime Field", field=field)
            if not is_mixed:
                container.set_title(field.type.name)
                container.set_inline(False)

                title = f"{field.type.name} (Date)"
                try:
                    assert field.value is not None
                    text = self.__driver.settings.format_datetime(
                        DatetimePicker.string2dt(field.value)
                    )
                except (ValueError, AssertionError):
                    title += " (Unknown Format)"
                    text = str(field.value)

                field_widget = TextFieldWidget(title, text)
                container.set_field_widget(field_widget)

                modal = PanelModal(
                    DatetimePicker(self.__driver, field.value or dt.now()),
                    title=f"Edit {field.type.name}",
                    save_callback=(
                        lambda content: (
                            self.update_field(field, content),  # type: ignore
                            self.update_from_entry(self.__cached_entries[0].id),
                        )
                    ),
                )

                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=remove_field_prompt(field.type.name),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_from_entry(self.__cached_entries[0].id),
                        ),
                    )
                )
            else:
                text = "<i>Mixed Data</i>"
                title = f"{field.type.name} (Wacky Date)"
                field_widget = TextFieldWidget(title, text)
                container.set_field_widget(field_widget)
        else:
            logger.warning("[FieldListController][write_container] Unknown Field", field=field)
            container.set_title(field.type.name)
            container.set_inline(False)
            title = f"{field.type.name} (Unknown Field Type)"
            field_widget = TextFieldWidget(title, field.type.name)
            container.set_field_widget(field_widget)
            container.set_remove_callback(
                lambda: self.remove_message_box(
                    prompt=remove_field_prompt(field.type.name),
                    callback=lambda: (
                        self.remove_field(field),
                        self.update_from_entry(self.__cached_entries[0].id),
                    ),
                )
            )

        container.setHidden(False)

    def write_tag_container(
        self, index: int, tags: set[Tag], category_tag: Tag | None = None, is_mixed: bool = False
    ) -> None:
        """Update/Create tag data for a FieldContainer.

        Args:
            index(int): The container index.
            tags(set[Tag]): The list of tags for this container.
            category_tag(Tag|None): The category tag this container represents.
            is_mixed(bool): Relevant when multiple items are selected.

            If True, field is not present in all selected items.
        """
        logger.info("[FieldListController][write_tag_container]", index=index)

        if len(self.field_containers) < (index + 1):
            container: FieldContainer = FieldContainer()
            self.field_containers.append(container)
            self.scroll_layout.addWidget(container)
        else:
            container = self.field_containers[index]

        container.set_title("Tags" if not category_tag else category_tag.name)
        container.set_inline(False)

        if not is_mixed:
            field_widget: QWidget | None = container.get_field_widget()

            if isinstance(field_widget, TagBoxWidget):
                with catch_warnings(record=True):
                    field_widget.on_update.disconnect()

            else:
                field_widget = TagBoxWidget(
                    "Tags",
                    self.__driver,
                )
                assert isinstance(field_widget, TagBoxWidget)

                container.set_field_widget(field_widget)

            field_widget.set_entries([entry.id for entry in self.__cached_entries])
            field_widget.set_tags(tags)

            field_widget.on_update.connect(
                lambda: (self.update_from_entry(self.__cached_entries[0].id, update_badges=True))
            )
        else:
            text: str = "<i>Mixed Data</i>"
            mixed_tags_widget: TextFieldWidget = TextFieldWidget("Mixed Tags", text)
            container.set_field_widget(mixed_tags_widget)

        container.setHidden(False)

    def remove_field(self, field: BaseField) -> None:
        """Remove a field from all selected Entries."""
        logger.info(
            "[FieldListController] Removing Field",
            field=field,
            selected=[entry.path for entry in self.__cached_entries],
        )

        entry_ids: list[int] = [entry.id for entry in self.__cached_entries]
        self.__lib.remove_entry_field(field, entry_ids)

    def update_field(self, field: BaseField, content: str) -> None:
        """Update a field in all selected Entries, given a field object."""
        assert isinstance(
            field,
            TextField | DatetimeField,
        ), f"instance: {type(field)}"

        entry_ids: list[int] = [e.id for e in self.__cached_entries]

        assert entry_ids, "No entries selected"
        self.__lib.update_entry_field(
            entry_ids,
            field,
            content,
        )

    def remove_message_box(self, prompt: str, callback: Callable) -> None:
        remove_mb: QMessageBox = QMessageBox()
        remove_mb.setText(prompt)
        remove_mb.setWindowTitle("Remove Field")
        remove_mb.setIcon(QMessageBox.Icon.Warning)
        cancel_button: QPushButton | None = remove_mb.addButton(
            Translations["generic.cancel_alt"], QMessageBox.ButtonRole.DestructiveRole
        )
        remove_mb.addButton("&Remove", QMessageBox.ButtonRole.RejectRole)
        if cancel_button is not None:
            remove_mb.setEscapeButton(cancel_button)
        result = remove_mb.exec_()
        if result == QMessageBox.ButtonRole.ActionRole.value:
            callback()
