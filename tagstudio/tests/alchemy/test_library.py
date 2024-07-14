import random
import string
from copy import copy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.core.library import Tag
from src.core.library.alchemy import Entry
from src.core.library.alchemy import Library
from src.core.library.alchemy.enums import TagColor, FilterState
from src.core.library.alchemy.fields import DEFAULT_FIELDS


def generate_entry(*, path: Path = None) -> Entry:
    if not path:
        # TODO - be sure no collision happens
        name = "".join(random.choices(string.ascii_lowercase, k=10))
        path = Path(name)

    return Entry(
        path=path,
    )


@pytest.fixture
def tag_fixture():
    def inner(**kwargs):
        params = dict(name="foo", color=TagColor.red) | kwargs
        return Tag(**params)

    yield inner


@pytest.mark.skip
def test_library_bootstrap():
    with TemporaryDirectory() as tmp_dir:
        lib = Library()
        lib.open_library(tmp_dir)
        assert lib.engine


def test_library_add_file():
    """Check Entry.path handling for insert vs lookup"""
    with TemporaryDirectory() as tmp_dir:
        # create file in tmp_dir
        file_path = Path(tmp_dir) / "bar.txt"
        file_path.write_text("bar")

        entry = Entry(path=file_path)

        lib = Library()
        lib.open_library(tmp_dir)
        assert not lib.has_item(entry.path)

        assert lib.add_entries([entry])

        assert lib.has_item(entry.path)


def test_create_tag(library, tag_fixture):
    # tag already exists
    assert not library.add_tag(tag_fixture())

    # new tag name
    assert library.add_tag(tag_fixture(name="bar"))


def test_library_search(library, tag_fixture):
    entries = library.entries
    tag = tag_fixture()
    assert len(entries) == 1, entries
    assert [x.name for x in entries[0].tags] == [tag.name]

    query_count, items = library.search_library(
        FilterState(
            name=tag.name,  # TODO - is this the query we want?
        ),
    )
    assert query_count == 1
    assert len(items) == 1
    entry = items[0]
    assert [x.name for x in entry.tags] == [tag.name]

    assert entry.tag_box_fields


def test_tag_search(library):
    tag = library.tags[0]

    assert library.search_tags(
        FilterState(name=tag.name),
    )
    assert not library.search_tags(
        FilterState(name=tag.name * 2),
    )


@pytest.mark.parametrize(
    ["file_path", "exists"],
    [
        (Path("foo.txt"), True),
        (Path("bar.txt"), False),
    ],
)
def test_has_item(library, file_path, exists):
    assert library.has_item(file_path) is exists, f"mismatch with item {file_path}"


def test_get_entry(library):
    entry = library.entries[0]
    assert entry.id

    _, entries = library.search_library(FilterState(id=entry.id))
    assert len(entries) == 1
    entry = entries[0]
    assert entry.path
    assert entry.tags


def test_entries_count(library):
    entries = [generate_entry() for _ in range(10)]
    library.add_entries(entries)
    matches, page = library.search_library(
        FilterState(
            page_size=5,
        )
    )

    assert matches == 11
    assert len(page) == 5


def test_add_field_to_entry(library):
    # Given
    item_path = Path("xxx")
    entry = generate_entry(path=item_path)
    # meta tags present
    assert len(entry.tag_box_fields) == 1

    library.add_entries([entry])

    # TODO - do this better way
    for field_idx, item in enumerate(DEFAULT_FIELDS):
        if item.name == "Tags":
            break

    # When
    library.add_field_to_entry(entry, field_idx)

    # Then
    entry = [x for x in library.entries if x.path == item_path][0]
    # meta tags and tags field present
    assert len(entry.tag_box_fields) == 2
