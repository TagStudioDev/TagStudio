from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from src.core.enums import DefaultEnum, LibraryPrefs
from src.core.library.alchemy import Entry, Library
from src.core.library.alchemy.enums import FilterState
from src.core.library.alchemy.fields import TextField, _FieldID
from src.core.library.alchemy.models import Tag


def test_library_add_alias(library, generate_tag):
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag

    parent_ids: set[int] = set()
    alias_ids: set[int] = set()
    alias_names: set[str] = set()
    alias_names.add("test_alias")
    library.update_tag(tag, parent_ids, alias_names, alias_ids)
    alias_ids = library.get_tag(tag.id).alias_ids

    assert len(alias_ids) == 1


def test_library_get_alias(library, generate_tag):
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag

    parent_ids: set[int] = set()
    alias_ids: set[int] = set()
    alias_names: set[str] = set()
    alias_names.add("test_alias")
    library.update_tag(tag, parent_ids, alias_names, alias_ids)
    alias_ids = library.get_tag(tag.id).alias_ids

    assert library.get_alias(tag.id, alias_ids[0]).name == "test_alias"


def test_library_update_alias(library, generate_tag):
    tag: Tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag

    parent_ids: set[int] = set()
    alias_ids: set[int] = set()
    alias_names: set[str] = set()
    alias_names.add("test_alias")
    library.update_tag(tag, parent_ids, alias_names, alias_ids)
    alias_ids = library.get_tag(tag.id).alias_ids

    assert library.get_alias(tag.id, alias_ids[0]).name == "test_alias"

    alias_names.remove("test_alias")
    alias_names.add("alias_update")
    library.update_tag(tag, parent_ids, alias_names, alias_ids)

    tag = library.get_tag(tag.id)
    assert len(tag.alias_ids) == 1
    assert library.get_alias(tag.id, tag.alias_ids[0]).name == "alias_update"


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_library_add_file(library):
    """Check Entry.path handling for insert vs lookup"""

    entry = Entry(
        path=Path("bar.txt"),
        folder=library.folder,
        fields=library.default_fields,
    )

    assert not library.has_path_entry(entry.path)
    assert library.add_entries([entry])
    assert library.has_path_entry(entry.path)


def test_create_tag(library, generate_tag):
    # tag already exists
    assert not library.add_tag(generate_tag("foo", id=1000))

    # new tag name
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag
    assert tag.id == 123

    tag_inc = library.add_tag(generate_tag("yyy"))
    assert tag_inc.id > 1000


def test_tag_self_parent(library, generate_tag):
    # tag already exists
    assert not library.add_tag(generate_tag("foo", id=1000))

    # new tag name
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag
    assert tag.id == 123

    library.update_tag(tag, {tag.id}, {}, {})
    tag = library.get_tag(tag.id)
    assert len(tag.parent_ids) == 0


def test_library_search(library, generate_tag, entry_full):
    assert library.entries_count == 2
    tag = list(entry_full.tags)[0]

    results = library.search_library(
        FilterState.from_tag_name(tag.name),
    )

    assert results.total_count == 1
    assert len(results) == 1


def test_tag_search(library):
    tag = library.tags[0]

    assert library.search_tags(tag.name.lower())
    assert library.search_tags(tag.name.upper())
    assert library.search_tags(tag.name[2:-2])
    assert library.search_tags(tag.name * 2) == [set(), set()]


def test_get_entry(library: Library, entry_min):
    assert entry_min.id
    result = library.get_entry_full(entry_min.id)
    assert result
    assert len(result.tags) == 1


def test_entries_count(library):
    entries = [Entry(path=Path(f"{x}.txt"), folder=library.folder, fields=[]) for x in range(10)]
    new_ids = library.add_entries(entries)
    assert len(new_ids) == 10

    results = library.search_library(FilterState.show_all().with_page_size(5))

    assert results.total_count == 12
    assert len(results) == 5


def test_parents_add(library, generate_tag):
    # Given
    tag: Tag = library.tags[0]
    assert tag.id is not None

    parent_tag = generate_tag("parent_tag_01")
    parent_tag = library.add_tag(parent_tag)
    assert parent_tag.id is not None

    # When
    assert library.add_parent_tag(tag.id, parent_tag.id)

    # Then
    assert tag.id is not None
    tag = library.get_tag(tag.id)
    assert tag.parent_ids


def test_remove_tag(library, generate_tag):
    tag = library.add_tag(generate_tag("food", id=123))

    assert tag

    tag_count = len(library.tags)

    library.remove_tag(tag)
    assert len(library.tags) == tag_count - 1


@pytest.mark.parametrize("is_exclude", [True, False])
def test_search_filter_extensions(library, is_exclude):
    # Given
    entries = list(library.get_entries())
    assert len(entries) == 2, entries

    library.set_prefs(LibraryPrefs.IS_EXCLUDE_LIST, is_exclude)
    library.set_prefs(LibraryPrefs.EXTENSION_LIST, ["md"])

    # When
    results = library.search_library(
        FilterState.show_all(),
    )

    # Then
    assert results.total_count == 1
    assert len(results) == 1

    entry = results[0]
    assert (entry.path.suffix == ".txt") == is_exclude


def test_search_library_case_insensitive(library):
    # Given
    entries = list(library.get_entries(with_joins=True))
    assert len(entries) == 2, entries

    entry = entries[0]
    tag = list(entry.tags)[0]

    # When
    results = library.search_library(
        FilterState.from_tag_name(tag.name.upper()),
    )

    # Then
    assert results.total_count == 1
    assert len(results) == 1

    assert results[0].id == entry.id


def test_preferences(library):
    for pref in LibraryPrefs:
        assert library.prefs(pref) == pref.default


def test_remove_entry_field(library, entry_full):
    title_field = entry_full.text_fields[0]

    library.remove_entry_field(title_field, [entry_full.id])

    entry = next(library.get_entries(with_joins=True))
    assert not entry.text_fields


def test_remove_field_entry_with_multiple_field(library, entry_full):
    # Given
    title_field = entry_full.text_fields[0]

    # When
    # add identical field
    assert library.add_field_to_entry(entry_full.id, field_id=title_field.type_key)

    # remove entry field
    library.remove_entry_field(title_field, [entry_full.id])

    # Then one field should remain
    entry = next(library.get_entries(with_joins=True))
    assert len(entry.text_fields) == 1


def test_update_entry_field(library, entry_full):
    title_field = entry_full.text_fields[0]

    library.update_entry_field(
        entry_full.id,
        title_field,
        "new value",
    )

    entry = next(library.get_entries(with_joins=True))
    assert entry.text_fields[0].value == "new value"


def test_update_entry_with_multiple_identical_fields(library, entry_full):
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
    entry = next(library.get_entries(with_joins=True))
    assert entry.text_fields[0].value == ""
    assert entry.text_fields[1].value == "new value"


def test_mirror_entry_fields(library: Library, entry_full):
    # new entry
    target_entry = Entry(
        folder=library.folder,
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
    new_entry = library.get_entry_full(entry_id)

    # mirror fields onto new entry
    library.mirror_entry_fields(new_entry, entry_full)

    # get new entry from library again
    entry = library.get_entry_full(entry_id)

    # make sure fields are there after getting it from the library again
    assert len(entry.fields) == 2
    assert {x.type_key for x in entry.fields} == {
        _FieldID.TITLE.name,
        _FieldID.NOTES.name,
    }


def test_merge_entries(library: Library):
    a = Entry(
        folder=library.folder,
        path=Path("a"),
        fields=[
            TextField(type_key=_FieldID.AUTHOR.name, value="Author McAuthorson", position=0),
            TextField(type_key=_FieldID.DESCRIPTION.name, value="test description", position=2),
        ],
    )
    b = Entry(
        folder=library.folder,
        path=Path("b"),
        fields=[TextField(type_key=_FieldID.NOTES.name, value="test note", position=1)],
    )
    try:
        ids = library.add_entries([a, b])
        entry_a = library.get_entry_full(ids[0])
        entry_b = library.get_entry_full(ids[1])
        tag_0 = library.add_tag(Tag(id=1000, name="tag_0"))
        tag_1 = library.add_tag(Tag(id=1001, name="tag_1"))
        tag_2 = library.add_tag(Tag(id=1002, name="tag_2"))
        library.add_tags_to_entries(ids[0], [tag_0.id, tag_2.id])
        library.add_tags_to_entries(ids[1], [tag_1.id])
        library.merge_entries(entry_a, entry_b)
        assert library.has_path_entry(Path("b"))
        assert not library.has_path_entry(Path("a"))
        fields = [field.value for field in entry_a.fields]
        assert "Author McAuthorson" in fields
        assert "test description" in fields
        assert "test note" in fields
        assert b.has_tag(tag_0) and b.has_tag(tag_1) and b.has_tag(tag_2)
    except AttributeError:
        AssertionError()


def test_remove_tags_from_entries(library, entry_full):
    removed_tag_id = -1
    for tag in entry_full.tags:
        removed_tag_id = tag.id
        library.remove_tags_from_entries(entry_full.id, tag.id)

    entry = next(library.get_entries(with_joins=True))
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
def test_search_entry_id(library: Library, query_name: int, has_result):
    result = library.get_entry(query_name)

    assert (result is not None) == has_result


def test_update_field_order(library, entry_full):
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
    entry = next(library.get_entries(with_joins=True))
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
    results = library.search_library(FilterState.from_path("bar.md"))
    assert results.total_count == 1
    assert len(results.items) == 1


def test_path_search_like(library: Library):
    results = library.search_library(FilterState.from_path("BAR.MD"))
    assert results.total_count == 0
    assert len(results.items) == 0


def test_path_search_default_with_sep(library: Library):
    results = library.search_library(FilterState.from_path("one/two"))
    assert results.total_count == 1
    assert len(results.items) == 1


def test_path_search_glob_after(library: Library):
    results = library.search_library(FilterState.from_path("foo*"))
    assert results.total_count == 1
    assert len(results.items) == 1


def test_path_search_glob_in_front(library: Library):
    results = library.search_library(FilterState.from_path("*bar.md"))
    assert results.total_count == 1
    assert len(results.items) == 1


def test_path_search_glob_both_sides(library: Library):
    results = library.search_library(FilterState.from_path("*one/two*"))
    assert results.total_count == 1
    assert len(results.items) == 1


def test_path_search_ilike_glob_equality(library: Library):
    results_ilike = library.search_library(FilterState.from_path("one/two"))
    results_glob = library.search_library(FilterState.from_path("*one/two*"))
    assert [e.id for e in results_ilike.items] == [e.id for e in results_glob.items]
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(FilterState.from_path("bar.md"))
    results_glob = library.search_library(FilterState.from_path("*bar.md*"))
    assert [e.id for e in results_ilike.items] == [e.id for e in results_glob.items]
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(FilterState.from_path("bar"))
    results_glob = library.search_library(FilterState.from_path("*bar*"))
    assert [e.id for e in results_ilike.items] == [e.id for e in results_glob.items]
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(FilterState.from_path("bar.md"))
    results_glob = library.search_library(FilterState.from_path("*bar.md*"))
    assert [e.id for e in results_ilike.items] == [e.id for e in results_glob.items]
    results_ilike, results_glob = None, None


def test_path_search_like_glob_equality(library: Library):
    results_ilike = library.search_library(FilterState.from_path("ONE/two"))
    results_glob = library.search_library(FilterState.from_path("*ONE/two*"))
    assert [e.id for e in results_ilike.items] == [e.id for e in results_glob.items]
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(FilterState.from_path("BAR.MD"))
    results_glob = library.search_library(FilterState.from_path("*BAR.MD*"))
    assert [e.id for e in results_ilike.items] == [e.id for e in results_glob.items]
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(FilterState.from_path("BAR.MD"))
    results_glob = library.search_library(FilterState.from_path("*bar.md*"))
    assert [e.id for e in results_ilike.items] != [e.id for e in results_glob.items]
    results_ilike, results_glob = None, None

    results_ilike = library.search_library(FilterState.from_path("bar.md"))
    results_glob = library.search_library(FilterState.from_path("*BAR.MD*"))
    assert [e.id for e in results_ilike.items] != [e.id for e in results_glob.items]
    results_ilike, results_glob = None, None


@pytest.mark.parametrize(["filetype", "num_of_filetype"], [("md", 1), ("txt", 1), ("png", 0)])
def test_filetype_search(library, filetype, num_of_filetype):
    results = library.search_library(FilterState.from_filetype(filetype))
    assert len(results.items) == num_of_filetype


@pytest.mark.parametrize(["filetype", "num_of_filetype"], [("png", 2), ("apng", 1), ("ng", 0)])
def test_filetype_return_one_filetype(file_mediatypes_library, filetype, num_of_filetype):
    results = file_mediatypes_library.search_library(FilterState.from_filetype(filetype))
    assert len(results.items) == num_of_filetype


@pytest.mark.parametrize(["mediatype", "num_of_mediatype"], [("plaintext", 2), ("image", 0)])
def test_mediatype_search(library, mediatype, num_of_mediatype):
    results = library.search_library(FilterState.from_mediatype(mediatype))
    assert len(results.items) == num_of_mediatype
