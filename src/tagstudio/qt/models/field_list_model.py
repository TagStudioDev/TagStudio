import typing

import structlog
from PySide6.QtCore import Qt

from tagstudio.core.library.alchemy.fields import BaseField, DatetimeField, TextField
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry, Tag

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class FieldListModel:
    def __init__(self, driver: "QtDriver") -> None:
        self.__lib: Library = driver.lib
        self.__driver: QtDriver = driver

        self.common_fields: list = []
        self.mixed_fields: list = []
        self.cached_entries: list[Entry] = []

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

    def remove_field(self, field: BaseField) -> None:
        """Remove a field from all selected Entries."""
        logger.info(
            "[FieldListController] Removing Field",
            field=field,
            selected=[entry.path for entry in self.cached_entries],
        )

        entry_ids: list[int] = [entry.id for entry in self.cached_entries]
        self.__lib.remove_entry_field(field, entry_ids)

    def update_field(self, field: BaseField, content: str) -> None:
        """Update a field in all selected Entries, given a field object."""
        assert isinstance(
            field,
            TextField | DatetimeField,
        ), f"instance: {type(field)}"

        entry_ids: list[int] = [e.id for e in self.cached_entries]

        assert entry_ids, "No entries selected"
        self.__lib.update_entry_field(
            entry_ids,
            field,
            content,
        )

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
