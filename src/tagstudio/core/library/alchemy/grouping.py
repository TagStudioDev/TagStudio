# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


"""Grouping strategies for organizing library entries."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library


class GroupingType(Enum):
    """Types of grouping strategies available."""

    NONE = "none"
    TAG = "tag"
    FILETYPE = "filetype"


@dataclass(frozen=True)
class GroupingCriteria:
    """Defines what to group by.

    Attributes:
        type: The type of grouping to apply.
        value: Optional value for the grouping (e.g., tag_id for TAG type).
    """

    type: GroupingType
    value: Any | None = None


@dataclass(frozen=True)
class EntryGroup:
    """Represents a group of entries.

    Attributes:
        key: The grouping key (Tag object, filetype string, etc.).
        entry_ids: List of entry IDs in this group.
        is_special: Whether this is a special group (e.g., "No Tag").
        special_label: Label for special groups.
        metadata: Flexible metadata dict for group-specific data.
    """

    key: Any
    entry_ids: list[int]
    is_special: bool = False
    special_label: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class GroupedSearchResult:
    """Container for grouped search results.

    Attributes:
        total_count: Total number of entries across all groups.
        groups: List of EntryGroup objects.
    """

    total_count: int
    groups: list[EntryGroup]

    @property
    def all_entry_ids(self) -> list[int]:
        """Flatten all entry IDs from all groups for backward compatibility."""
        result: list[int] = []
        for group in self.groups:
            result.extend(group.entry_ids)
        return result

    def __bool__(self) -> bool:
        """Boolean evaluation for the wrapper."""
        return self.total_count > 0

    def __len__(self) -> int:
        """Return the total number of entries across all groups."""
        return self.total_count


class GroupingStrategy(ABC):
    """Abstract base class for grouping implementations."""

    @abstractmethod
    def group_entries(
        self, lib: "Library", entry_ids: list[int], criteria: GroupingCriteria
    ) -> GroupedSearchResult:
        """Group entries according to criteria.

        Args:
            lib: Library instance.
            entry_ids: List of entry IDs to group.
            criteria: Grouping criteria.

        Returns:
            GroupedSearchResult with entries organized into EntryGroup objects.
        """
        pass

    @abstractmethod
    def get_display_name(self, group: EntryGroup) -> str:
        """Get display name for a group.

        Args:
            group: The entry group.

        Returns:
            Human-readable name for the group.
        """
        pass
