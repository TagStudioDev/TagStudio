from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory

import pytest
from src.core.enums import DefaultEnum, LibraryPrefs
from src.core.library.alchemy import Entry, Library
from src.core.library.alchemy.enums import FilterState
from src.core.library.alchemy.fields import TextField, _FieldID


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
    assert not library.add_tag(generate_tag("foo"))

    # new tag name
    tag = library.add_tag(generate_tag("xxx", id=123))
    assert tag
    assert tag.id == 123

    tag_inc = library.add_tag(generate_tag("yyy"))
    assert tag_inc.id > 1000


def test_library_search(library, generate_tag, entry_full):
    assert library.entries_count == 2
    tag = list(entry_full.tags)[0]

    results = library.search_library(
        FilterState(
            tag=tag.name,
        ),
    )

    assert results.total_count == 1
    assert len(results) == 1

    entry = results[0]
    assert {x.name for x in entry.tags} == {
        "foo",
    }

    assert entry.tag_box_fields


def test_tag_search(library):
    tag = library.tags[0]

    assert library.search_tags(
        FilterState(tag=tag.name.lower()),
    )

    assert library.search_tags(
        FilterState(tag=tag.name.upper()),
    )

    assert library.search_tags(FilterState(tag=tag.name[2:-2]))

    assert not library.search_tags(
        FilterState(tag=tag.name * 2),
    )


def test_get_entry(library, entry_min):
    assert entry_min.id
    results = library.search_library(FilterState(id=entry_min.id))
    assert len(results) == results.total_count == 1
    assert results[0].tags


def test_entries_count(library):
    entries = [Entry(path=Path(f"{x}.txt"), folder=library.folder, fields=[]) for x in range(10)]
    new_ids = library.add_entries(entries)
    assert len(new_ids) == 10

    results = library.search_library(
        FilterState(
            page_size=5,
        )
    )

    assert results.total_count == 12
    assert len(results) == 5


def test_add_field_to_entry(library):
    # Given
    entry = Entry(
        folder=library.folder,
        path=Path("xxx"),
        fields=library.default_fields,
    )
    # meta tags + content tags
    assert len(entry.tag_box_fields) == 2

    assert library.add_entries([entry])

    # When
    library.add_entry_field_type(entry.id, field_id=_FieldID.TAGS)

    # Then
    entry = [x for x in library.get_entries(with_joins=True) if x.path == entry.path][0]
    # meta tags and tags field present
    assert len(entry.tag_box_fields) == 3


def test_add_field_tag(library, entry_full, generate_tag):
    # Given
    tag_name = "xxx"
    tag = generate_tag(tag_name)
    tag_field = entry_full.tag_box_fields[0]

    # When
    library.add_field_tag(entry_full, tag, tag_field.type_key)

    # Then
    results = library.search_library(FilterState(id=entry_full.id))
    tag_field = results[0].tag_box_fields[0]
    assert [x.name for x in tag_field.tags if x.name == tag_name]


def test_subtags_add(library, generate_tag):
    # Given
    tag = library.tags[0]
    assert tag.id is not None

    subtag = generate_tag("subtag1")
    subtag = library.add_tag(subtag)
    assert subtag.id is not None

    # When
    assert library.add_subtag(tag.id, subtag.id)

    # Then
    assert tag.id is not None
    tag = library.get_tag(tag.id)
    assert tag.subtag_ids


@pytest.mark.parametrize("is_exclude", [True, False])
def test_search_filter_extensions(library, is_exclude):
    # Given
    entries = list(library.get_entries())
    assert len(entries) == 2, entries

    library.set_prefs(LibraryPrefs.IS_EXCLUDE_LIST, is_exclude)
    library.set_prefs(LibraryPrefs.EXTENSION_LIST, ["md"])

    # When
    results = library.search_library(
        FilterState(),
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
        FilterState(tag=tag.name.upper()),
    )

    # Then
    assert results.total_count == 1
    assert len(results) == 1

    assert results[0].id == entry.id


def test_preferences(library):
    for pref in LibraryPrefs:
        assert library.prefs(pref) == pref.default


def test_save_windows_path(library, generate_tag):
    # pretend we are on windows and create `Path`

    entry = Entry(
        path=PureWindowsPath("foo\\bar.txt"),
        folder=library.folder,
        fields=library.default_fields,
    )
    tag = generate_tag("win_path")
    tag_name = tag.name

    library.add_entries([entry])
    # library.add_tag(tag)
    library.add_field_tag(entry, tag, create_field=True)

    results = library.search_library(FilterState(tag=tag_name))
    assert results

    # path should be saved in posix format
    assert str(results[0].path) == "foo/bar.txt"


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
    assert library.add_entry_field_type(entry_full.id, field_id=title_field.type_key)

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
    library.add_entry_field_type(entry_full.id, field_id=title_field.type_key)

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


def test_mirror_entry_fields(library, entry_full):
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

    entry_id = library.add_entries([target_entry])[0]

    results = library.search_library(FilterState(id=entry_id))
    new_entry = results[0]

    library.mirror_entry_fields(new_entry, entry_full)

    results = library.search_library(FilterState(id=entry_id))
    entry = results[0]

    assert len(entry.fields) == 4
    assert {x.type_key for x in entry.fields} == {
        _FieldID.TITLE.name,
        _FieldID.NOTES.name,
        _FieldID.TAGS_META.name,
        _FieldID.TAGS.name,
    }


def test_remove_tag_from_field(library, entry_full):
    for field in entry_full.tag_box_fields:
        for tag in field.tags:
            removed_tag = tag.name
            library.remove_tag_from_field(tag, field)
            break

    entry = next(library.get_entries(with_joins=True))
    for field in entry.tag_box_fields:
        assert removed_tag not in [tag.name for tag in field.tags]


@pytest.mark.parametrize(
    ["query_name", "has_result"],
    [
        ("foo", 1),  # filename substring
        ("bar", 1),  # filename substring
        ("one", 0),  # path, should not match
    ],
)
def test_search_file_name(library, query_name, has_result):
    results = library.search_library(
        FilterState(name=query_name),
    )

    assert results.total_count == has_result


@pytest.mark.parametrize(
    ["query_name", "has_result"],
    [
        (1, 1),
        ("1", 1),
        ("xxx", 0),
        (222, 0),
    ],
)
def test_search_entry_id(library, query_name, has_result):
    results = library.search_library(
        FilterState(id=query_name),
    )

    assert results.total_count == has_result


def test_update_field_order(library, entry_full):
    # Given
    title_field = entry_full.text_fields[0]

    # When add two more fields
    library.add_entry_field_type(entry_full.id, field_id=title_field.type_key, value="first")
    library.add_entry_field_type(entry_full.id, field_id=title_field.type_key, value="second")

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


def test_path_search_glob_after(library: Library):
    results = library.search_library(FilterState(path="foo*"))
    assert results.total_count == 1
    assert len(results.items) == 1


def test_path_search_glob_in_front(library: Library):
    results = library.search_library(FilterState(path="*bar.md"))
    assert results.total_count == 1
    assert len(results.items) == 1


def test_path_search_glob_both_sides(library: Library):
    results = library.search_library(FilterState(path="*one/two*"))
    assert results.total_count == 1
    assert len(results.items) == 1


@pytest.mark.parametrize(["filetype", "num_of_filetype"], [("md", 1), ("txt", 1), ("png", 0)])
def test_filetype_search(library, filetype, num_of_filetype):
    results = library.search_library(FilterState(filetype=filetype))
    assert len(results.items) == num_of_filetype


@pytest.mark.parametrize(["filetype", "num_of_filetype"], [("png", 2), ("apng", 1), ("ng", 0)])
def test_filetype_return_one_filetype(file_mediatypes_library, filetype, num_of_filetype):
    results = file_mediatypes_library.search_library(FilterState(filetype=filetype))
    assert len(results.items) == num_of_filetype


@pytest.mark.parametrize(["mediatype", "num_of_mediatype"], [("plaintext", 2), ("image", 0)])
def test_mediatype_search(library, mediatype, num_of_mediatype):
    results = library.search_library(FilterState(mediatype=mediatype))
    assert len(results.items) == num_of_mediatype
