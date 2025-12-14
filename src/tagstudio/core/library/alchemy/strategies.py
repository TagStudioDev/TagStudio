# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


"""Concrete grouping strategy implementations."""

from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from tagstudio.core.library.alchemy.constants import TAG_CHILDREN_ID_QUERY
from tagstudio.core.library.alchemy.grouping import (
    EntryGroup,
    GroupedSearchResult,
    GroupingCriteria,
    GroupingStrategy,
)
from tagstudio.core.library.alchemy.models import Entry, Tag

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library


class TagGroupingStrategy(GroupingStrategy):
    """Groups entries by tag hierarchy.

    When grouping by a parent tag, creates one group per child tag.
    Entries with multiple child tags appear in all applicable groups (duplicated).
    """

    def group_entries(
        self, lib: "Library", entry_ids: list[int], criteria: GroupingCriteria
    ) -> GroupedSearchResult:
        """Group entries by tag hierarchy.

        Args:
            lib: Library instance.
            entry_ids: List of entry IDs to group.
            criteria: Grouping criteria (value should be tag_id).

        Returns:
            GroupedSearchResult with entries organized by child tags.
        """
        if not entry_ids:
            return GroupedSearchResult(total_count=0, groups=[])

        tag_id = criteria.value
        if tag_id is None:
            return GroupedSearchResult(total_count=0, groups=[])

        # Get all child tag IDs (including the selected tag itself)
        with Session(lib.engine) as session:
            result = session.execute(TAG_CHILDREN_ID_QUERY, {"tag_id": tag_id})
            child_tag_ids = [row[0] for row in result]

        if not child_tag_ids:
            return GroupedSearchResult(total_count=0, groups=[])

        # Load tag objects
        tags_by_id: dict[int, Tag] = {}
        with Session(lib.engine) as session:
            for tag in session.scalars(select(Tag).where(Tag.id.in_(child_tag_ids))):
                tags_by_id[tag.id] = tag

        # Get which entries have which tags
        tag_to_entries = lib.get_tag_entries(child_tag_ids, entry_ids)

        # Build entry -> tags mapping
        entry_to_tags: dict[int, list[int]] = {entry_id: [] for entry_id in entry_ids}
        for tag_id_item, entries_with_tag in tag_to_entries.items():
            for entry_id in entries_with_tag:
                entry_to_tags[entry_id].append(tag_id_item)

        # Build groups per child tag (entries can appear in multiple groups)
        tag_groups: dict[int, list[int]] = {}
        no_tag_entries: list[int] = []

        for entry_id in entry_ids:
            tags_on_entry = entry_to_tags[entry_id]

            if not tags_on_entry:
                # Entry has no child tags
                no_tag_entries.append(entry_id)
            else:
                # Add entry to ALL child tag groups it belongs to
                for tag_id_item in tags_on_entry:
                    if tag_id_item not in tag_groups:
                        tag_groups[tag_id_item] = []
                    tag_groups[tag_id_item].append(entry_id)

        # Create EntryGroup objects
        groups: list[EntryGroup] = []

        # Sort child tags alphabetically and create groups (only for non-empty groups)
        sorted_tag_ids = sorted(tag_groups.keys(), key=lambda tid: tags_by_id[tid].name.lower())
        for tag_id_item in sorted_tag_ids:
            groups.append(
                EntryGroup(
                    key=tags_by_id[tag_id_item],
                    entry_ids=tag_groups[tag_id_item],
                    is_special=False,
                )
            )

        # Add "No Tag" group (collapsed by default)
        if no_tag_entries:
            groups.append(
                EntryGroup(
                    key=None,
                    entry_ids=no_tag_entries,
                    is_special=True,
                    special_label="No Tag",
                )
            )

        return GroupedSearchResult(total_count=len(entry_ids), groups=groups)

    def get_display_name(self, group: EntryGroup) -> str:
        """Get display name for a tag group.

        Args:
            group: The entry group.

        Returns:
            Tag name or special label.
        """
        if group.is_special and group.special_label:
            return group.special_label
        if isinstance(group.key, Tag):
            return group.key.name
        return str(group.key)


class FiletypeGroupingStrategy(GroupingStrategy):
    """Groups entries by file extension."""

    def group_entries(
        self, lib: "Library", entry_ids: list[int], criteria: GroupingCriteria
    ) -> GroupedSearchResult:
        """Group entries by file extension.

        Args:
            lib: Library instance.
            entry_ids: List of entry IDs to group.
            criteria: Grouping criteria (value not used).

        Returns:
            GroupedSearchResult with entries organized by filetype.
        """
        if not entry_ids:
            return GroupedSearchResult(total_count=0, groups=[])

        # Load entries
        with Session(lib.engine) as session:
            entries = session.scalars(select(Entry).where(Entry.id.in_(entry_ids))).all()

        # Group by file extension
        filetype_groups: dict[str, list[int]] = {}
        for entry in entries:
            ext = Path(entry.path).suffix.lower()
            if not ext:
                ext = "(no extension)"
            filetype_groups.setdefault(ext, []).append(entry.id)

        # Create EntryGroup objects sorted by extension
        groups = [
            EntryGroup(key=ext, entry_ids=ids) for ext, ids in sorted(filetype_groups.items())
        ]

        return GroupedSearchResult(total_count=len(entry_ids), groups=groups)

    def get_display_name(self, group: EntryGroup) -> str:
        """Get display name for a filetype group.

        Args:
            group: The entry group.

        Returns:
            File extension or label.
        """
        return str(group.key)
