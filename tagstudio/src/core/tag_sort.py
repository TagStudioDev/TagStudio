from enum import Enum, Flag, auto
from typing import Any, Callable

from src.core.constants import TAG_COLORS
from src.core.library import Library


class TagSortProperty(int, Enum):
    MATCHES_PREFIX = auto()
    CATEGORY = auto()
    LINEAGE_DEPTH = auto()
    DESCENDENT_COUNT = auto()
    NAME = auto()
    COLOR = auto()
    ID = auto()


class TagSortDirection(Flag):
    ASC = False
    DESC = True


Sort = list[tuple[TagSortProperty, TagSortDirection]]

# _default_sort must contain LINEAGE_DEPTH and ID
_default_sort: Sort = [
    (TagSortProperty.LINEAGE_DEPTH, TagSortDirection.DESC),
    (TagSortProperty.DESCENDENT_COUNT, TagSortDirection.DESC),
    (TagSortProperty.NAME, TagSortDirection.ASC),
    (TagSortProperty.COLOR, TagSortDirection.ASC),
    (TagSortProperty.ID, TagSortDirection.ASC),
]

def normalize_sort(old_sort: Sort = None) -> Sort:
    if old_sort is None:
        old_sort = []
    old_sort.extend(_default_sort.copy())

    sorted_properties: set[TagSortProperty] = set()
    new_sort = []
    for sort_property, sort_direction in old_sort:
        if sort_property not in sorted_properties:
            sorted_properties.add(sort_property)
            new_sort.append((sort_property, sort_direction))

    return new_sort


def add_sort_property(
    new_property: TagSortProperty,
    new_direction: TagSortDirection,
    old_sort: Sort = None,
) -> Sort:
    new_sort = [(new_property, new_direction)]

    if old_sort is not None:
        new_sort.extend(old_sort)

    return normalize_sort(new_sort)


def reverse_sort(old_sort: Sort) -> Sort:
    new_sort: Sort = []
    for sort_property, sort_direction in old_sort:
        if sort_direction is TagSortDirection.ASC:
            new_direction = TagSortDirection.DESC
        else:
            new_direction = TagSortDirection.ASC

        new_sort.append((sort_property, new_direction))
    return new_sort


def get_key(
    lib: Library, tag_id_list, sort: Sort = None
) -> Callable[[int], list[Any]]:
    if sort is None:
        sort = _default_sort.copy()
    
    sort = normalize_sort(sort)

    outer_sort: Sort = []
    lineage_direction: TagSortDirection
    inner_sort: Sort = []

    outer = True
    for sort_property, sort_direction in sort:
        if sort_property is TagSortProperty.LINEAGE_DEPTH:
            outer = False
            lineage_direction = sort_direction
            continue

        if outer:
            outer_sort.append((sort_property, sort_direction))
        else:
            inner_sort.append((sort_property, sort_direction))

    if lineage_direction is TagSortDirection.DESC:
        inner_sort = reverse_sort(inner_sort)
    def key(tag_id: int) -> list[Any]:
        nonlocal lineage_direction
        canonical_lineage: Any = _get_canonical_lineage(
            lib, outer_sort, inner_sort, tag_id, tag_id_list
        )
        if lineage_direction is TagSortDirection.DESC:
            canonical_lineage = _ReverseComparison(canonical_lineage)

        key_items = _get_basic_key_items(lib, tag_id, outer_sort)
        key_items.append(canonical_lineage)

        print(key_items)
        return key_items

    return key


def _get_basic_key_items(
    lib: Library, tag_id: int, sort: Sort, tag_id_set: set[int] = None, prefix: str = None
) -> list[Any]:
    key_items = []
    for sort_property, sort_direction in sort:
        key_item: Any = None
        match sort_property:
            case TagSortProperty.MATCHES_PREFIX:
                key_item = lib.get_tag(tag_id).name.lower().startswith(prefix.lower())
            # case TagSortProperty.CATEGORY:
            # case TagSortProperty.LINEAGE_DEPTH:
            case TagSortProperty.DESCENDENT_COUNT:
                tag_cluster = lib.get_tag_cluster(tag_id)
                if tag_id_set is not None:
                    key_item = len(tag_id_set.intersection(set(tag_cluster)))
                else:
                    key_item = len(tag_cluster)
            case TagSortProperty.NAME:
                key_item = lib.get_tag(tag_id).display_name(lib)
            case TagSortProperty.COLOR:
                key_item = TAG_COLORS.index(lib.get_tag(tag_id).color.lower())
            case TagSortProperty.ID:
                key_item = tag_id

        if sort_direction is TagSortDirection.DESC:
            key_item = _ReverseComparison(key_item)

        key_items.append(key_item)

    return key_items


class _ReverseComparison:
    def __init__(self, inner: Any):
        self.inner = inner

    def __lt__(self, other):
        return other.inner.__lt__(self.inner)

    def __le__(self, other):
        return other.inner.__le__(self.inner)

    def __eq__(self, other):
        return other.inner.__eq__(self.inner)

    def __ne__(self, other):
        return other.inner.__ne__(self.inner)

    def __gt__(self, other):
        return other.inner.__gt__(self.inner)

    def __ge__(self, other):
        return other.inner.__ge__(self.inner)
    
    def __str__(self) -> str:
        return f"rev:{self.inner}"
    
    def __repr__(self) -> str:
        return str(self)

def _get_canonical_lineage(
    lib: Library,
    outer_sort: Sort,
    inner_sort: Sort,
    tag_id: int,
    tag_id_list: list[int],
    last_generation_ids=None,
    first_gen=True,
) -> list[list[Any]]:
    if first_gen:
        last_generation_ids = set([-1])
    
    ancestor_id_queue: list[int] = [tag_id]
    encountered_tag_ids: set[int] = set(last_generation_ids)
    encountered_tag_ids.add(tag_id)

    this_generation_ids: set[int] = set()

    while ancestor_id_queue:
        next_ancestor_id = ancestor_id_queue.pop()
        parent_ids: set[int] = set(lib.get_tag(next_ancestor_id).subtag_ids)

        if first_gen and not parent_ids:
            this_generation_ids.add(next_ancestor_id)

        if not first_gen and last_generation_ids.intersection(parent_ids):
            this_generation_ids.add(next_ancestor_id)

        #TODO: make this work for looping relationships
        for parent_id in parent_ids:
            if parent_id not in encountered_tag_ids:
                encountered_tag_ids.add(parent_id)
                ancestor_id_queue.append(parent_id)

    outer_key = _get_basic_key_items(lib, tag_id, outer_sort)
    first_in_generation_id = None
    first_in_generation_inner_key_item = None
    for challenger_id in this_generation_ids:
        if challenger_id not in tag_id_list:
            continue

        challenger_outer_key_item = _get_basic_key_items(lib, challenger_id, outer_sort)
        if challenger_outer_key_item != outer_key:
            continue

        challenger_inner_key_item = _get_basic_key_items(lib, challenger_id, inner_sort)
        if (
            first_in_generation_id is None
            or challenger_inner_key_item < first_in_generation_inner_key_item
        ):
            first_in_generation_id = challenger_id
            first_in_generation_inner_key_item = challenger_inner_key_item
    
    lineage: list[list[Any]] = []
    if first_in_generation_id is not None:
        lineage = [first_in_generation_inner_key_item]
        lineage.extend(
            _get_canonical_lineage(
                lib,
                outer_sort,
                inner_sort,
                tag_id,
                tag_id_list,
                set([first_in_generation_id]),
                False,
            )
        )
    elif this_generation_ids:
        lineage = _get_canonical_lineage(
            lib, outer_sort, inner_sort, tag_id, tag_id_list, this_generation_ids, False
        )
    
    return lineage
