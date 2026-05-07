# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import sys
import typing
from collections.abc import Callable
from datetime import datetime as dt
from warnings import catch_warnings

import structlog
from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
    QWidget,
)

from tagstudio.core.library.alchemy.enums import FieldTypeEnum
from tagstudio.core.library.alchemy.fields import (
    BaseField,
    BaseFieldTemplate,
    DatetimeField,
    TextField,
)
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry, Tag
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.field_container_controller import FieldContainer
from tagstudio.qt.controllers.tag_box_controller import TagBoxWidget
from tagstudio.qt.mixed.datetime_picker import DatetimePicker
from tagstudio.qt.models.field_list_model import FieldListModel
from tagstudio.qt.translations import FIELD_TYPE_KEYS, Translations
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


def remove_message_box(prompt: str, callback: Callable) -> None:
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


class FieldListController(FieldListView):
    """A list of field containers."""

    def __init__(self, library: Library, driver: "QtDriver") -> None:
        super().__init__()

        self.__lib: Library = library
        self.__driver: QtDriver = driver

        # Can't be private as other things rely on it...
        self.model: FieldListModel = FieldListModel(driver)

    def update_from_entry(self, entry_id: int, update_badges: bool = True) -> None:
        """Update tags and fields from a single Entry source."""
        logger.warning("[FieldListController] Updating Selection", entry_id=entry_id)

        entry: Entry = unwrap(self.__lib.get_entry_full(entry_id))
        self.model.cached_entries = [entry]
        self.update_granular(entry.tags, entry.fields, update_badges)

    def update_granular(
        self, entry_tags: set[Tag], entry_fields: list[BaseField], update_badges: bool = True
    ) -> None:
        """Individually update elements of the item preview."""
        num_containers: int = len(entry_fields)
        container_index: int = 0

        # Write tag container(s)
        if entry_tags:
            categories: dict[Tag | None, set[Tag]] = self.model.get_tag_categories(entry_tags)
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
        entry: Entry = self.model.cached_entries[0]
        tag: Tag | None = self.__lib.get_tag(tag_id)

        if not tag:
            return

        if toggle_value:
            entry.tags.add(tag)
        else:
            entry.tags.discard(tag)

        self.update_granular(entry_tags=entry.tags, entry_fields=entry.fields, update_badges=False)

    def write_container(self, index: int, field: BaseField, is_mixed: bool = False) -> None:
        """Update/Create data for a FieldContainer.

        Args:
            index(int): The container index.
            field(BaseField): The type of field to write to.
            is_mixed(bool): Relevant when multiple items are selected.

            If True, field is not present in all selected items.
        """
        logger.info(
            "[FieldListController][write_container]",
            index=index,
            name=field.name,
            type=field.class_name,
        )
        if len(self.field_containers) < (index + 1):
            container: FieldContainer = FieldContainer()
            self.add_field_container(container)
        else:
            container = self.field_containers[index]

        # Set field title
        field_name_key: str = FIELD_TYPE_KEYS.get(field.class_name, "field_type.unknown")
        title = f"{field.name} ({Translations[field_name_key]})"

        # Single-line Text
        if type(field) is TextField and not field.is_multiline:
            container.set_title(field.name)
            container.set_inline(False)

            # Normalize line endings in any text content.
            if not is_mixed:
                assert isinstance(field.value, str | type(None))
                text: str = field.value if isinstance(field.value, str) else ""
            else:
                text = "<i>Mixed Data</i>"  # TODO: Localize this

            field_widget: TextFieldWidget = TextFieldWidget(title, text)
            container.set_field_widget(field_widget)
            if not is_mixed:
                modal: PanelModal = PanelModal(
                    EditTextLine(field.value),
                    title=title,
                    window_title=f"Edit {field.name}",  # TODO: Localize this
                    save_callback=(  # pyright: ignore[reportArgumentType]
                        lambda content: (
                            self.update_text_field(field, content, is_multiline=False),
                            self.update_from_entry(self.model.cached_entries[0].id),
                        )
                    ),
                )
                if "pytest" in sys.modules:
                    # for better testability
                    container.modal = modal  # pyright: ignore[reportAttributeAccessIssue]

                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: remove_message_box(
                        prompt=remove_field_prompt(title),
                        callback=lambda: (
                            self.model.remove_field(field),
                            self.update_from_entry(self.model.cached_entries[0].id),
                        ),
                    )
                )

        # Multiline Text
        elif type(field) is TextField and field.is_multiline:
            container.set_title(field.name)
            container.set_inline(False)
            # Normalize line endings in any text content.
            if not is_mixed:
                assert isinstance(field.value, str | type(None))
                text = (field.value if isinstance(field.value, str) else "").replace("\r", "\n")
            else:
                text = "<i>Mixed Data</i>"  # TODO: Localize this
            field_widget = TextFieldWidget(title, text)
            container.set_field_widget(field_widget)
            if not is_mixed:
                modal = PanelModal(
                    EditTextBox(field.value),
                    title=title,
                    window_title=f"Edit {field.name}",  # TODO: Localize this
                    save_callback=(  # pyright: ignore[reportArgumentType]
                        lambda content: (
                            self.update_text_field(field, content, is_multiline=True),
                            self.update_from_entry(self.model.cached_entries[0].id),
                        )
                    ),
                )
                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: remove_message_box(
                        prompt=remove_field_prompt(field.name),
                        callback=lambda: (
                            self.model.remove_field(field),
                            self.update_from_entry(self.model.cached_entries[0].id),
                        ),
                    )
                )

        elif type(field) is DatetimeField:
            logger.info("[FieldListController][write_container] Datetime Field", field=field)
            if not is_mixed:
                container.set_title(field.name)
                container.set_inline(False)

                try:
                    assert field.value is not None
                    text = self.__driver.settings.format_datetime(
                        DatetimePicker.string2dt(field.value)
                    )
                except (ValueError, AssertionError):
                    text = str(field.value)

                field_widget = TextFieldWidget(title, text)
                container.set_field_widget(field_widget)

                modal = PanelModal(
                    DatetimePicker(self.__driver, field.value or dt.now()),
                    title=f"Edit {field.name}",
                    save_callback=(  # pyright: ignore[reportArgumentType]
                        lambda content: (
                            self.update_datetime_field(field, content),
                            self.update_from_entry(self.model.cached_entries[0].id),
                        )
                    ),
                )

                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: remove_message_box(
                        prompt=remove_field_prompt(field.name),
                        callback=lambda: (
                            self.model.remove_field(field),
                            self.update_from_entry(self.model.cached_entries[0].id),
                        ),
                    )
                )
            else:
                text = "<i>Mixed Data</i>"  # TODO: Localize this
                field_widget = TextFieldWidget(title, text)
                container.set_field_widget(field_widget)
        else:
            logger.warning(
                "[FieldListController][write_container] Unknown Field", field=field
            )  # TODO: Localize this
            container.set_title(field.name)
            container.set_inline(False)
            field_widget = TextFieldWidget(title, field.name)
            container.set_field_widget(field_widget)
            container.set_remove_callback(
                lambda: remove_message_box(
                    prompt=remove_field_prompt(field.name),
                    callback=lambda: (
                        self.model.remove_field(field),
                        self.update_from_entry(self.model.cached_entries[0].id),
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
            self.add_field_container(container)
        else:
            container = self.field_containers[index]

        container.set_title(
            "Tags" if not category_tag else category_tag.name
        )  # TODO: Localize this
        container.set_inline(False)

        if not is_mixed:
            field_widget: QWidget | None = container.get_field_widget()

            if isinstance(field_widget, TagBoxWidget):
                with catch_warnings(record=True):
                    field_widget.on_update.disconnect()

            else:
                field_widget = TagBoxWidget(
                    "Tags",  # TODO: Localize this
                    self.__driver,
                )
                assert isinstance(field_widget, TagBoxWidget)

                container.set_field_widget(field_widget)

            field_widget.set_entries([entry.id for entry in self.model.cached_entries])
            field_widget.set_tags(tags)

            field_widget.on_update.connect(
                lambda: (
                    self.update_from_entry(self.model.cached_entries[0].id, update_badges=True)
                )
            )
        else:
            text: str = "<i>Mixed Data</i>"
            mixed_tags_widget: TextFieldWidget = TextFieldWidget("Mixed Tags", text)
            container.set_field_widget(mixed_tags_widget)

        container.setHidden(False)

    def update_text_field(self, field: TextField, value: str, is_multiline: bool) -> None:
        """Update a text field across selected entries."""
        entry_ids: list[int] = [e.id for e in self.cached_entries]
        assert entry_ids, "No entries selected"

        self.__lib.update_text_field(entry_ids, field, value, is_multiline)

    def update_datetime_field(self, field: DatetimeField, value: str):
        """Update a datetime field across selected entries."""
        entry_ids = [e.id for e in self.__model.cached_entries]
        assert entry_ids, "No entries selected"

        self.__lib.update_datetime_field(entry_ids, field, dt.fromisoformat(value))
