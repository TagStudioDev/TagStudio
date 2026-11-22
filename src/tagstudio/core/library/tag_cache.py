# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from collections.abc import Iterable
from threading import Lock
from typing import NamedTuple

import structlog
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from tagstudio.core.library.alchemy.enums import MAX_SQL_VARIABLES
from tagstudio.core.library.alchemy.joins import CategoryExclusion, TagParent
from tagstudio.core.library.alchemy.models import Tag, TagAlias, TagColorGroup

logger = structlog.get_logger(__name__)


class TagColor(NamedTuple):
    primary: str
    secondary: str | None
    color_border: bool


class CachedTag(NamedTuple):
    """Cached data for a Tag."""

    id: int
    name: str
    shorthand: str | None
    aliases: tuple[str, ...]
    color: TagColor | None
    disambiguation_id: int | None
    is_category: bool
    parent_ids: tuple[int, ...]
    exclusion_ids: tuple[int, ...]  # Excluded category tag IDs


class TagCacheData(NamedTuple):
    tags: dict[int, CachedTag]
    names: dict[int, str]  # Casefolded names
    joined_aliases: dict[int, str]  # Casefolded shorthands and aliases, joined as single strings
    children: dict[int, tuple[int, ...]]


# NOTE: A null separator is used to join a tag's shorthand and aliases into a single string,
# which is much faster to match against compared to several different strings.
_SEPARATOR = "\0"


class TagCache:
    """An in-memory copy of all tag data used for searching and displaying.

    All additions, deletions, and edits are synced with the database.
    """

    def __init__(self, engine: Engine | None) -> None:
        self._engine = engine
        self._data: TagCacheData | None = None
        self._write_lock = Lock()
        self._refresh_count = 0  # Used to tell if tags were edited during a database read

    def load(self) -> TagCacheData:
        """Return the cached data, reading every tag first if it isn't loaded yet."""
        data = self._data
        while data is None:
            refresh_count = self._refresh_count
            loaded = TagCacheData(tags={}, names={}, joined_aliases={}, children={})
            _add_tags(loaded, self._read_cached_tags(None))
            with self._write_lock:
                if refresh_count == self._refresh_count:
                    self._data = loaded
            data = self._data
        return data

    def refresh_tags(self, tag_ids: Iterable[int]) -> None:
        """Re-read these tags after they were added, edited, or removed."""
        with self._write_lock:
            self._refresh_count += 1
            data = self._data
            if data is None:
                return
            refreshed_ids = set(tag_ids)
            try:
                tags = self._read_cached_tags(refreshed_ids)
            except Exception as e:
                logger.error("[TagCache] Could not read edited tags, reloading later", error=e)
                self._data = None
                return
            self._data = _refreshed_data(data, refreshed_ids, tags)

    def search(self, query: str) -> list[int]:
        """Return IDs of tags whose display name, shorthand, or alias contains the query.

        Display names starting with the query come first, shortest first, and descendants come
        last. An empty query returns every tag.
        """
        data = self.load()
        query = query.casefold()

        def sorted_by_name(tag_ids: Iterable[int]) -> list[int]:
            return sorted(tag_ids, key=lambda tag_id: data.names[tag_id])

        if not query:
            return sorted_by_name(data.tags)

        # TODO: Look into ignoring spaces and punctuation, possibly with an option to override that
        display_names = {
            tag_id: _display_name(data, tag.name, tag.disambiguation_id).casefold()
            for tag_id, tag in data.tags.items()
            if tag.disambiguation_id is not None
        }
        matches = {tag_id for tag_id, text in data.names.items() if query in text}
        matches.update(tag_id for tag_id, text in display_names.items() if query in text)
        matches.update(tag_id for tag_id, text in data.joined_aliases.items() if query in text)
        descendants = _with_descendants(data, matches) - matches
        # TODO: Rank with tunable weights for things like exact matches, aliases, parents, etc.
        ranked = sorted_by_name(matches) + sorted_by_name(descendants)
        if not query.strip():
            return ranked

        starting_with_query = [
            tag_id
            for tag_id in ranked
            if display_names.get(tag_id, data.names[tag_id]).startswith(query)
        ]
        starting_with_query.sort(key=lambda tag_id: len(data.tags[tag_id].name))
        starting_ids = set(starting_with_query)
        return starting_with_query + [tag_id for tag_id in ranked if tag_id not in starting_ids]

    def get(self, tag_id: int) -> CachedTag | None:
        """Return the tag with this ID, or `None` if it's missing."""
        return self.load().tags.get(tag_id)

    def tag_ids_by_name(self, name: str) -> set[int]:
        """Return the IDs of tags with a name, shorthand, or alias equal to this name.

        Case-insensitive. Spaces and underscores are interchangeable.
        """
        data = self.load()
        name = name.casefold().replace(" ", "_")
        tag_ids = {tag_id for tag_id, text in data.names.items() if text.replace(" ", "_") == name}
        tag_ids.update(
            tag_id
            for tag_id, text in data.joined_aliases.items()
            if name in text.replace(" ", "_").split(_SEPARATOR)
        )
        return tag_ids

    def with_descendants(self, tag_ids: Iterable[int]) -> set[int]:
        """Return these tag IDs plus the IDs of all their descendant tags."""
        return _with_descendants(self.load(), tag_ids)

    def display_name(self, name: str, disambiguation_id: int | None) -> str:
        """Return the tag name followed by the disambiguation tag's shorthand (if one) or name."""
        return _display_name(self.load(), name, disambiguation_id)

    def _read_cached_tags(self, tag_ids: set[int] | None) -> dict[int, CachedTag]:
        """Read the tag cache's data for these tags, or for every tag if `tag_ids` is `None`."""
        if tag_ids is not None and len(tag_ids) > MAX_SQL_VARIABLES:
            id_list = list(tag_ids)
            cached_tags: dict[int, CachedTag] = {}
            for i in range(0, len(id_list), MAX_SQL_VARIABLES):
                cached_tags.update(self._read_cached_tags(set(id_list[i : i + MAX_SQL_VARIABLES])))
            return cached_tags

        tag_query = select(
            Tag.id,
            Tag.name,
            Tag.shorthand,
            Tag.disambiguation_id,
            Tag.is_category,
            TagColorGroup.primary,
            TagColorGroup.secondary,
            TagColorGroup.color_border,
        ).outerjoin(Tag.color)
        alias_query = select(TagAlias.tag_id, TagAlias.name)
        link_query = select(TagParent.parent_id, TagParent.child_id)
        exclusion_query = select(CategoryExclusion.tag_id, CategoryExclusion.category_id)
        if tag_ids is not None:
            tag_query = tag_query.where(Tag.id.in_(tag_ids))
            alias_query = alias_query.where(TagAlias.tag_id.in_(tag_ids))
            link_query = link_query.where(TagParent.child_id.in_(tag_ids))
            exclusion_query = exclusion_query.where(CategoryExclusion.tag_id.in_(tag_ids))

        with Session(self._engine) as session:
            alias_names: dict[int, list[str]] = {}
            for tag_id, alias_name in session.execute(alias_query):
                alias_names.setdefault(tag_id, []).append(alias_name)
            parent_ids: dict[int, list[int]] = {}
            for parent_id, child_id in session.execute(link_query):
                parent_ids.setdefault(child_id, []).append(parent_id)
            exclusion_ids: dict[int, list[int]] = {}
            for tag_id, category_id in session.execute(exclusion_query):
                exclusion_ids.setdefault(tag_id, []).append(category_id)
            cached_tags = {}
            for (
                tag_id,
                name,
                shorthand,
                disambiguation_id,
                is_category,
                primary,
                secondary,
                color_border,
            ) in session.execute(tag_query):
                tag_color = None
                if primary is not None:
                    tag_color = TagColor(primary, secondary, color_border)
                cached_tags[tag_id] = CachedTag(
                    tag_id,
                    name,
                    shorthand,
                    tuple(alias_names.get(tag_id, ())),
                    tag_color,
                    disambiguation_id,
                    is_category,
                    tuple(parent_ids.get(tag_id, ())),
                    tuple(exclusion_ids.get(tag_id, ())),
                )
        return cached_tags


def _refreshed_data(
    data: TagCacheData, tag_ids: set[int], tags: dict[int, CachedTag]
) -> TagCacheData:
    """Build and return a refreshed `TagCacheData` object, removing any missing from `tags`."""
    updated = TagCacheData(
        tags=dict(data.tags),
        names=dict(data.names),
        joined_aliases=dict(data.joined_aliases),
        children=dict(data.children),
    )
    for tag_id in tag_ids:
        old_tag = updated.tags.pop(tag_id, None)
        updated.names.pop(tag_id, None)
        updated.joined_aliases.pop(tag_id, None)
        if old_tag is None:
            continue
        for parent_id in old_tag.parent_ids:
            siblings = tuple(
                child for child in updated.children.get(parent_id, ()) if child != tag_id
            )
            if siblings:
                updated.children[parent_id] = siblings
            else:
                updated.children.pop(parent_id, None)
    _add_tags(updated, tags)
    for tag_id in tag_ids - updated.tags.keys():
        updated.children.pop(tag_id, None)
    return updated


def _add_tags(data: TagCacheData, tags: dict[int, CachedTag]) -> None:
    data.tags.update(tags)
    children: dict[int, list[int]] = {}
    for tag_id, tag in tags.items():
        data.names[tag_id] = tag.name.casefold()
        alias_names = (tag.shorthand, *tag.aliases) if tag.shorthand else tag.aliases
        if alias_names:
            data.joined_aliases[tag_id] = _SEPARATOR.join(alias_names).casefold()
        for parent_id in tag.parent_ids:
            children.setdefault(parent_id, []).append(tag_id)
    for parent_id, child_ids in children.items():
        data.children[parent_id] = (*data.children.get(parent_id, ()), *child_ids)


def _with_descendants(data: TagCacheData, tag_ids: Iterable[int]) -> set[int]:
    found = set(tag_ids)
    pending = list(found)
    while pending:
        for child_id in data.children.get(pending.pop(), ()):
            if child_id not in found:
                found.add(child_id)
                pending.append(child_id)
    return found


def _display_name(data: TagCacheData, name: str, disambiguation_id: int | None) -> str:
    if disambiguation_id is None:
        return name
    disambiguation_tag = data.tags.get(disambiguation_id)
    if disambiguation_tag is None:
        return "<NO DISAM TAG>"
    return f"{name} ({disambiguation_tag.shorthand or disambiguation_tag.name})"
