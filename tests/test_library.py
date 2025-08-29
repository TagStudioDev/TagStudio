# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import structlog

from tagstudio.core.enums import DefaultEnum, LibraryPrefs
from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.fields import (
    TextField,
    _FieldID,  # pyright: ignore[reportPrivateUsage]
)
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry, Tag
from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger()


def test_library_add_alias(library: Library, generate_tag: Callable[..., Tag]):
    tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    parent_ids: set[int] = set()
    alias_ids: set[int] = set()
    alias_names: set[str] = set()
    alias_names.add("test_alias")
    library.update_tag(tag, parent_ids, alias_names, alias_ids)
    tag = unwrap(library.get_tag(tag.id))
    alias_ids = set(tag.alias_ids)

    assert len(alias_ids) == 1


def test_library_get_alias(library: Library, generate_tag: Callable[..., Tag]):
    tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    parent_ids: set[int] = set()
    alias_ids: list[int] = []
    alias_names: set[str] = set()
    alias_names.add("test_alias")
    library.update_tag(tag, parent_ids, alias_names, alias_ids)
    tag = unwrap(library.get_tag(tag.id))
    alias_ids = tag.alias_ids

    alias = unwrap(library.get_alias(tag.id, alias_ids[0]))
    assert alias.name == "test_alias"


def test_library_update_alias(library: Library, generate_tag: Callable[..., Tag]):
    tag: Tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))

    parent_ids: set[int] = set()
    alias_ids: list[int] = []
    alias_names: set[str] = set()
    alias_names.add("test_alias")
    library.update_tag(tag, parent_ids, alias_names, alias_ids)
    tag = unwrap(library.get_tag(tag.id))
    alias_ids = tag.alias_ids

    alias = unwrap(library.get_alias(tag.id, alias_ids[0]))
    assert alias.name == "test_alias"

    alias_names.remove("test_alias")
    alias_names.add("alias_update")
    library.update_tag(tag, parent_ids, alias_names, alias_ids)

    tag = unwrap(library.get_tag(tag.id))
    assert len(tag.alias_ids) == 1
    alias = unwrap(library.get_alias(tag.id, tag.alias_ids[0]))
    assert alias.name == "alias_update"


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_library_add_file(library: Library):
    """Check Entry.path handling for insert vs lookup"""
    entry = Entry(
        path=Path("bar.txt"),
        folder=unwrap(library.folder),
        fields=library.default_fields,
    )

    assert not library.has_path_entry(entry.path)
    assert library.add_entries([entry])
    assert library.has_path_entry(entry.path)


def test_create_tag(library: Library, generate_tag: Callable[..., Tag]):
    # tag already exists
    assert library.add_tag(generate_tag("foo", id=1000)) is None

    # new tag name
    tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))
    assert tag.id == 123

    tag_inc = unwrap(library.add_tag(generate_tag("yyy")))
    assert tag_inc.id > 1000


def test_tag_self_parent(library: Library, generate_tag: Callable[..., Tag]):
    # tag already exists
    assert library.add_tag(generate_tag("foo", id=1000)) is None

    # new tag name
    tag = unwrap(library.add_tag(generate_tag("xxx", id=123)))
    assert tag.id == 123

    library.update_tag(tag, {tag.id}, [], [])
    tag = unwrap(library.get_tag(tag.id))
    assert len(tag.parent_ids) == 0


def test_library_search(library: Library, entry_full: Entry):
    assert library.entries_count == 2
    tag = list(entry_full.tags)[0]

    results = library.search_library(
        BrowsingState.from_tag_name(tag.name),
        page_size=500,
    )

    assert results.total_count == 1
    assert len(results) == 1


def test_tag_search(library: Library):
    tag = library.tags[0]

    assert library.search_tags(tag.name.lower())
    assert library.search_tags(tag.name.upper())
    assert library.search_tags(tag.name[2:-2])
    assert library.search_tags(tag.name * 2) == [set(), set()]


def test_get_entry(library: Library, entry_min: Entry):
    result = unwrap(library.get_entry_full(unwrap(entry_min.id)))
    assert len(result.tags) == 1


def test_entries_count(library: Library):
    folder = unwrap(library.folder)
    entries = [Entry(path=Path(f"{x}.txt"), folder=folder, fields=[]) for x in range(10)]
    new_ids = library.add_entries(entries)
    assert len(new_ids) == 10

    results = library.search_library(BrowsingState.show_all(), page_size=5)

    assert results.total_count == 12
    assert len(results) == 5


def test_parents_add(library: Library, generate_tag: Callable[..., Tag]):
    # Given
    tag: Tag = library.tags[0]

    parent_tag: Tag = generate_tag("parent_tag_01")
    parent_tag = unwrap(library.add_tag(parent_tag))

    # When
    assert library.add_parent_tag(tag.id, unwrap(parent_tag.id))

    # Then
    tag = unwrap(library.get_tag(unwrap(tag.id)))
    assert tag.parent_ids


def test_remove_tag(library: Library, generate_tag: Callable[..., Tag]):
    tag = unwrap(library.add_tag(generate_tag("food", id=123)))

    tag_count = len(library.tags)

    library.remove_tag(tag)
    assert len(library.tags) == tag_count - 1


def test_search_library_case_insensitive(library: Library):
    # Given
    entries = list(library.all_entries(with_joins=True))
    assert len(entries) == 2, entries

    entry = entries[0]
    tag = list(entry.tags)[0]

    # When
    results = library.search_library(
        BrowsingState.from_tag_name(tag.name.upper()),
        page_size=500,
    )

    # Then
    assert results.total_count == 1
    assert len(results) == 1

    assert results[0] == entry.id


def test_preferences(library: Library):
    for pref in LibraryPrefs:
        assert library.prefs(pref) == pref.default


def test_remove_entry_field(library: Library, entry_full: Entry):
    title_field = entry_full.text_fields[0]

    library.remove_entry_field(title_field, [entry_full.id])

    entry = next(library.all_entries(with_joins=True))
    assert not entry.text_fields


def test_remove_field_entry_with_multiple_field(library: Library, entry_full: Entry):
    # Given
    title_field = entry_full.text_fields[0]

    # When
    # add identical field
    assert library.add_field_to_entry(entry_full.id, field_id=title_field.type_key)

    # remove entry field
    library.remove_entry_field(title_field, [entry_full.id])

    # Then one field should remain
    entry = next(library.all_entries(with_joins=True))
    assert len(entry.text_fields) == 1


def test_update_entry_field(library: Library, entry_full: Entry):
    title_field = entry_full.text_fields[0]

    library.update_entry_field(
        entry_full.id,
        title_field,
        "new value",
    )

    entry = next(library.all_entries(with_joins=True))
    assert entry.text_fields[0].value == "new value"


def test_update_entry_with_multiple_identical_fields(library: Library, entry_full: Entry):
    # Given
    title_field = entry_full.text_fields[0]

    # When
    # add identical field
    library.add_field_to_entry(entry_full.id, field_id=title_field.type_key)

    # update one of the fields
    library.update_entry_field(
        entry_full.id,
        title_field,
        "new value",
    )

    # Then only one should be updated
    entry = next(library.all_entries(with_joins=True))
    assert entry.text_fields[0].value == ""
    assert entry.text_fields[1].value == "new value"


def test_mirror_entry_fields(library: Library, entry_full: Entry):
    # new entry
    target_entry = Entry(
        folder=unwrap(library.folder),
        path=Path("xxx"),
        fields=[
            TextField(
                type_key=_FieldID.NOTES.name,
                value="notes",
                position=0,
            )
        ],
    )

    # insert new entry and get id
    entry_id = library.add_entries([target_entry])[0]

    # get new entry from library
    new_entry = unwrap(library.get_entry_full(entry_id))

    # mirror fields onto new entry
    library.mirror_entry_fields(new_entry, entry_full)

    # get new entry from library again
    entry = unwrap(library.get_entry_full(entry_id))

    # make sure fields are there after getting it from the library again
    assert len(entry.fields) == 2
    assert {x.type_key for x in entry.fields} == {
        _FieldID.TITLE.name,
        _FieldID.NOTES.name,
    }


def test_merge_entries(library: Library):
    folder = unwrap(library.folder)

    tag_0: Tag = unwrap(library.add_tag(Tag(id=1010, name="tag_0")))
    tag_1: Tag = unwrap(library.add_tag(Tag(id=1011, name="tag_1")))
    tag_2: Tag = unwrap(library.add_tag(Tag(id=1012, name="tag_2")))

    a = Entry(
        folder=folder,
        path=Path("a"),
        fields=[
            TextField(type_key=_FieldID.AUTHOR.name, value="Author McAuthorson", position=0),
            TextField(type_key=_FieldID.DESCRIPTION.name, value="test description", position=2),
        ],
    )
    b = Entry(
        folder=folder,
        path=Path("b"),
        fields=[TextField(type_key=_FieldID.NOTES.name, value="test note", position=1)],
    )
    ids = library.add_entries([a, b])

    library.add_tags_to_entries(ids[0], [tag_0.id, tag_2.id])
    library.add_tags_to_entries(ids[1], [tag_1.id])

    entry_a: Entry = unwrap(library.get_entry_full(ids[0]))
    entry_b: Entry = unwrap(library.get_entry_full(ids[1]))

    assert library.merge_entries(entry_a, entry_b)
    assert not library.has_path_entry(Path("a"))
    assert library.has_path_entry(Path("b"))

    entry_b_merged = unwrap(library.get_entry_full(ids[1]))

    fields = [field.value for field in entry_b_merged.fields]
    assert "Author McAuthorson" in fields
    assert "test description" in fields
    assert "test note" in fields
    b_tags = [t.id for t in entry_b_merged.tags]
    assert tag_0.id in b_tags
    assert tag_1.id in b_tags
    assert tag_2.id in b_tags


def test_remove_tags_from_entries(library: Library, entry_full: Entry):
    removed_tag_id = -1
    for tag in entry_full.tags:
        removed_tag_id = tag.id
        library.remove_tags_from_entries(entry_full.id, tag.id)

    entry = next(library.all_entries(with_joins=True))
    assert removed_tag_id not in [t.id for t in entry.tags]


@pytest.mark.parametrize(
    ["query_name", "has_result"],
    [
        (1, 1),
        ("1", 1),
        ("xxx", 0),
        (222, 0),
    ],
)
def test_search_entry_id(library: Library, query_name: int, has_result: bool):
    result = library.get_entry(query_name)

    assert (result is not None) == has_result


def test_update_field_order(library: Library, entry_full: Entry):
    # Given
    title_field = entry_full.text_fields[0]

    # When add two more fields
    library.add_field_to_entry(entry_full.id, field_id=title_field.type_key, value="first")
    library.add_field_to_entry(entry_full.id, field_id=title_field.type_key, value="second")

    # remove the one on first position
    assert title_field.position == 0
    library.remove_entry_field(title_field, [entry_full.id])

    # recalculate the positions
    library.update_field_position(
        type(title_field),
        title_field.type_key,
        entry_full.id,
    )

    # Then
    entry = next(library.all_entries(with_joins=True))
    assert entry.text_fields[0].position == 0
    assert entry.text_fields[0].value == "first"
    assert entry.text_fields[1].position == 1
    assert entry.text_fields[1].value == "second"


def test_library_prefs_multiple_identical_vals():
    # check the preferences are inherited from DefaultEnum
    assert issubclass(LibraryPrefs, DefaultEnum)

    # create custom settings with identical values
    class TestPrefs(DefaultEnum):
        FOO = 1
        BAR = 1

    assert TestPrefs.FOO.default == 1
    assert TestPrefs.BAR.default == 1
    assert TestPrefs.BAR.name == "BAR"

    # accessing .value should raise exception
    with pytest.raises(AttributeError):
        assert TestPrefs.BAR.value


def test_path_search_ilike(library: Library):
    results = library.search_library(BrowsingState.from_path("bar.md"), page_size=500)
    assert results.total_count == 1
    assert len(results.ids) == 1


def test_path_search_like(library: Library):
    results = library.search_library(BrowsingState.from_path("BAR.MD"), page_size=500)
    assert results.total_count == 0
    assert len(results.ids) == 0


def test_path_search_default_with_sep(library: Library):
    results = library.search_library(BrowsingState.from_path("one/two"), page_size=500)
    assert results.total_count == 1
    assert len(results.ids) == 1


def test_path_search_glob_after(library: Library):
    results = library.search_library(BrowsingState.from_path("foo*"), page_size=500)
    assert results.total_count == 1
    assert len(results.ids) == 1


def test_path_search_glob_in_front(library: Library):
    results = library.search_library(BrowsingState.from_path("*bar.md"), page_size=500)
    assert results.total_count == 1
    assert len(results.ids) == 1


def test_path_search_glob_both_sides(library: Library):
    results = library.search_library(BrowsingState.from_path("*one/two*"), page_size=500)
    assert results.total_count == 1
    assert len(results.ids) == 1


# TODO: deduplicate this code with pytest parametrisation or a for loop
def test_path_search_ilike_glob_equality(library: Library):
    results_ilike = library.search_library(BrowsingState.from_path("one/two"), page_size=500)
    results_glob = library.search_library(BrowsingState.from_path("*one/two*"), page_size=500)
    assert results_ilike.ids == results_glob.ids
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(BrowsingState.from_path("bar.md"), page_size=500)
    results_glob = library.search_library(BrowsingState.from_path("*bar.md*"), page_size=500)
    assert results_ilike.ids == results_glob.ids
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(BrowsingState.from_path("bar"), page_size=500)
    results_glob = library.search_library(BrowsingState.from_path("*bar*"), page_size=500)
    assert results_ilike.ids == results_glob.ids
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(BrowsingState.from_path("bar.md"), page_size=500)
    results_glob = library.search_library(BrowsingState.from_path("*bar.md*"), page_size=500)
    assert results_ilike.ids == results_glob.ids
    results_ilike, results_glob = None, None


# TODO: isn't this the exact same as the one before?
def test_path_search_like_glob_equality(library: Library):
    results_ilike = library.search_library(BrowsingState.from_path("ONE/two"), page_size=500)
    results_glob = library.search_library(BrowsingState.from_path("*ONE/two*"), page_size=500)
    assert results_ilike.ids == results_glob.ids
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(BrowsingState.from_path("BAR.MD"), page_size=500)
    results_glob = library.search_library(BrowsingState.from_path("*BAR.MD*"), page_size=500)
    assert results_ilike.ids == results_glob.ids
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(BrowsingState.from_path("BAR.MD"), page_size=500)
    results_glob = library.search_library(BrowsingState.from_path("*bar.md*"), page_size=500)
    assert results_ilike.ids != results_glob.ids
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(BrowsingState.from_path("bar.md"), page_size=500)
    results_glob = library.search_library(BrowsingState.from_path("*BAR.MD*"), page_size=500)
    assert results_ilike.ids != results_glob.ids
    results_ilike, results_glob = None, None


@pytest.mark.parametrize(["filetype", "num_of_filetype"], [("md", 1), ("txt", 1), ("png", 0)])
def test_filetype_search(library: Library, filetype: str, num_of_filetype: int):
    results = library.search_library(BrowsingState.from_filetype(filetype), page_size=500)
    assert len(results.ids) == num_of_filetype


@pytest.mark.parametrize(["filetype", "num_of_filetype"], [("png", 2), ("apng", 1), ("ng", 0)])
def test_filetype_return_one_filetype(
    file_mediatypes_library: Library, filetype: str, num_of_filetype: int
):
    results = file_mediatypes_library.search_library(
        BrowsingState.from_filetype(filetype), page_size=500
    )
    assert len(results.ids) == num_of_filetype


@pytest.mark.parametrize(["mediatype", "num_of_mediatype"], [("plaintext", 2), ("image", 0)])
def test_mediatype_search(library: Library, mediatype: str, num_of_mediatype: int):
    results = library.search_library(BrowsingState.from_mediatype(mediatype), page_size=500)
    assert len(results.ids) == num_of_mediatype
