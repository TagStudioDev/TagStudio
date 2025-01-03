# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import sys
import typing
from collections.abc import Callable
from datetime import datetime as dt

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
from src.core.enums import Theme
from src.core.library.alchemy.fields import (
    BaseField,
    DatetimeField,
    FieldTypeEnum,
    TextField,
)
from src.core.library.alchemy.library import Library
from src.qt.translations import Translations
from src.core.library.alchemy.models import Entry
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper
from src.qt.modals.add_field import AddFieldModal
from src.core.library.alchemy.models import Entry, Tag
from src.qt.widgets.fields import FieldContainer
from src.qt.widgets.panel import PanelModal
from src.qt.widgets.tag_box import TagBoxWidget
from src.qt.widgets.text import TextWidget
from src.qt.widgets.text_box_edit import EditTextBox
from src.qt.widgets.text_line_edit import EditTextLine

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class FieldContainers(QWidget):
    """The Preview Panel Widget."""

    tags_updated = Signal()

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()

        self.is_connected = False
        self.lib = library
        self.driver: QtDriver = driver
        self.initialized = False
        self.is_open: bool = False
        self.common_fields: list = []
        self.mixed_fields: list = []
        self.selected: list[Entry] = []
        self.containers: list[FieldContainer] = []

        self.panel_bg_color = (
            Theme.COLOR_BG_DARK.value
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.COLOR_BG_LIGHT.value
        )

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(6, 1, 6, 6)

        scroll_container: QWidget = QWidget()
        scroll_container.setObjectName("entryScrollContainer")
        scroll_container.setLayout(self.scroll_layout)

        info_section = QWidget()
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(6)

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
            "QWidget#entryScrollContainer{"
            f"background:{self.panel_bg_color};"
            "border-radius:6px;"
            "}"
        )
        self.scroll_area.setWidget(scroll_container)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scroll_area)

    def update_from_entry(self, entry: Entry):
        """Update tags and fields from a single Entry source."""
        self.selected = [self.lib.get_entry_full(entry.id)]
        logger.info(
            "[FieldContainers] Updating Selection",
            path=entry.path,
            fields=entry.fields,
            tags=entry.tags,
        )

        entry_ = self.selected[0]
        container_len: int = len(entry_.fields)
        container_index = 0

        # Write tag container(s)
        if entry_.tags:
            categories = self.get_tag_categories(entry_.tags)
            for cat, tags in sorted(categories.items(), key=lambda kv: (kv[0] is None, kv)):
                self.write_tag_container(
                    container_index, tags=tags, category_tag=cat, is_mixed=False
                )
                container_index += 1
                container_len += 1
        # Write field container(s)
        for index, field in enumerate(entry_.fields, start=container_index):
            self.write_container(index, field, is_mixed=False)

        # Hide leftover container(s)
        if len(self.containers) > container_len:
            for i, c in enumerate(self.containers):
                if i > (container_len - 1):
                    c.setHidden(True)

    def get_tag_categories(self, tags: set[Tag]) -> dict[Tag, set[Tag | None]]:
        """Get a dictionary of category tags mapped to their respective tags."""
        cats: dict[Tag, set[Tag | None]] = {}
        cats[None] = set()

        # Initialize all categories from parents
        for tag in tags:
            for p_tag in list(tag.subtags) + [tag]:
                logger.info(f"[{tag.name}] is {p_tag.name} a category? ({p_tag.is_category})")
                if p_tag.is_category:
                    cats[p_tag] = set()
        logger.info("Blank Tag Categories", cats=cats)

        # Add tags to any applicable categories
        for tag in tags:
            is_general = True
            for p_tag in list(cats.keys()):
                logger.info(f"[{tag.name}] Checking category tag key {p_tag}")
                if not p_tag:
                    pass
                elif p_tag in tag.subtags:
                    cats[p_tag].add(tag)
                    is_general = False
                elif tag == p_tag:
                    cats[p_tag].add(tag)
                    is_general = False
                    pass
            if is_general:
                cats[None].add(tag)

        # Remove unused categories
        empty: list[Tag] = []
        for k, v in list(cats.items()):
            if not v:
                empty.append(k)
        for key in empty:
            cats.pop(key, None)

        logger.info("Tag Categories", cats=cats)
        return cats

    def remove_field_prompt(self, name: str) -> str:
        return Translations.translate_formatted("library.field.confirm_remove", name=name)

    def add_field_to_selected(self, field_list: list):
        """Add list of entry fields to one or more selected items."""
        logger.info(
            "[FieldContainers][add_field_to_selected]",
            selected=[x.path for x in self.selected],
            fields=field_list,
        )
        for entry in self.selected:
            for field_item in field_list:
                self.lib.add_entry_field_type(
                    entry.id,
                    field_id=field_item.data(Qt.ItemDataRole.UserRole),
                )

    def add_tags_to_selected(self, tags: list[int]):
        """Add list of tags to one or more selected items."""
        logger.info(
            "[FieldContainers][add_tags_to_selected]",
            selected=[x.path for x in self.selected],
            tags=tags,
        )
        for entry in self.selected:
            self.lib.add_tags_to_entry(
                entry.id,
                tag_ids=tags,
            )

    def write_container(self, index: int, field: BaseField, is_mixed: bool = False):
        """Update/Create data for a FieldContainer.

        Args:
            index(int): The container index.
            field(BaseField): The type of field to write to.
            is_mixed(bool): Relevant when multiple items are selected.

            If True, field is not present in all selected items.
        """
        logger.info("[write_field_container]", index=index)
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
                            self.update_field(field, content),
                            self.update_from_entry(self.selected[0]),
                        )
                    ),
                )
                if "pytest" in sys.modules:
                    # for better testability
                    container.modal = modal  # type: ignore

                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.type.value),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_from_entry(self.selected[0]),
                        ),
                    )
                )

        elif field.type.type == FieldTypeEnum.TEXT_BOX:
            container.set_title(field.type.name)
            # container.set_editable(True)
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
                            self.update_field(field, content),
                            self.update_from_entry(self.selected[0]),
                        )
                    ),
                )
                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.name),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_from_entry(self.selected[0]),
                        ),
                    )
                )

        elif field.type.type == FieldTypeEnum.DATETIME:
            if not is_mixed:
                try:
                    container.set_title(field.type.name)
                    # container.set_editable(False)
                    container.set_inline(False)
                    # TODO: Localize this and/or add preferences.
                    date = dt.strptime(field.value, "%Y-%m-%d %H:%M:%S")
                    title = f"{field.type.name} (Date)"
                    inner_widget = TextWidget(title, date.strftime("%D - %r"))
                    container.set_inner_widget(inner_widget)
                except Exception:
                    container.set_title(field.type.name)
                    # container.set_editable(False)
                    container.set_inline(False)
                    title = f"{field.type.name} (Date) (Unknown Format)"
                    inner_widget = TextWidget(title, str(field.value))
                    container.set_inner_widget(inner_widget)

                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.name),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_from_entry(self.selected[0]),
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
                        self.update_from_entry(self.selected[0]),
                    ),
                )
            )

        container.edit_button.setHidden(True)
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
        logger.info("[write_tag_container]", index=index)
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
                logger.warning("recycling")
                inner_widget.set_tags(tags)
                try:
                    inner_widget.updated.disconnect()
                except RuntimeError:
                    logger.error("[FieldContainers] Failed to disconnect inner_container.updated")

            else:
                logger.warning("creating new")
                inner_widget = TagBoxWidget(
                    tags,
                    "Tags",
                    self.driver,
                )
                container.set_inner_widget(inner_widget)

            inner_widget.updated.connect(
                lambda: (
                    self.write_tag_container(index, tags, category_tag),
                    self.update_from_entry(self.selected[0]),
                )
            )
        else:
            text = "<i>Mixed Data</i>"
            inner_widget = TextWidget("Mixed Tags", text)
            container.set_inner_widget(inner_widget)

        self.tags_updated.emit()
        container.edit_button.setHidden(True)
        container.setHidden(False)

    def remove_field(self, field: BaseField):
        """Remove a field from all selected Entries."""
        logger.info(
            "[FieldContainers] Removing Field",
            field=field,
            selected=[x.path for x in self.selected],
        )
        entry_ids = [e.id for e in self.selected]
        self.lib.remove_entry_field(field, entry_ids)

        # # if the field is meta tags, update the badges
        # if field.type_key == _FieldID.TAGS_META.value:
        #     self.driver.update_badges(self.selected)

    def update_field(self, field: BaseField, content: str) -> None:
        """Update a field in all selected Entries, given a field object."""
        assert isinstance(
            field,
            (TextField, DatetimeField),  # , TagBoxField)
        ), f"instance: {type(field)}"

        entry_ids = [e.id for e in self.selected]

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
        # remove_mb.setStandardButtons(QMessageBox.StandardButton.Cancel)
        remove_mb.setDefaultButton(cancel_button)
        remove_mb.setEscapeButton(cancel_button)
        result = remove_mb.exec_()
        # logging.info(result)
        if result == 3:  # TODO - what is this magic number?
            callback()

    def set_tags_updated_slot(self, slot: object):
        """Replacement for tag_callback."""
        if self.is_connected:
            self.tags_updated.disconnect()

        logger.info("[FieldContainers][set_tags_updated_slot] Setting tags updated slot")
        self.tags_updated.connect(slot)
        self.is_connected = True
