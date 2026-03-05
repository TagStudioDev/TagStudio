# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import structlog

from tagstudio.core.library.alchemy.enums import BrowsingState, SortingModeEnum
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.query_lang.util import ParsingError
from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger()


def verify_count(lib: Library, query: str, count: int):
    results = lib.search_library(BrowsingState.from_search_query(query), page_size=500)
    logger.info("results", entry_ids=results.ids, count=results.total_count)
    assert results.total_count == count
    assert len(results.ids) == count


@pytest.mark.parametrize(
    ["query", "count"],
    [
        ("", 32),
        ("path:*", 32),
        ("path:*inherit*", 24),
        ("path:*comp*", 5),
        ("special:untagged", 3),
        ("filetype:png", 25),
        ("filetype:jpg", 6),
        ("filetype:'jpg'", 6),
        ("tag_id:1011", 5),
        ("tag_id:1038", 11),
        ("doesnt exist", 0),
        ("archived", 0),
        ("favorite", 0),
        ("tag:favorite", 0),
        ("circle", 11),
        ("tag:square", 11),
        ("green", 5),
        ("orange", 5),
        ("tag:orange", 5),
    ],
)
def test_single_constraint(search_library: Library, query: str, count: int):
    verify_count(search_library, query, count)


@pytest.mark.parametrize(
    ["query", "count"],
    [
        ("circle aND square", 5),
        ("circle square", 5),
        ("green AND square", 2),
        ("green square", 2),
        ("orange AnD square", 2),
        ("orange square", 2),
        ("orange and filetype:png", 5),
        ("square and filetype:jpg", 2),
        ("orange filetype:png", 5),
        ("green path:*inherit*", 4),
    ],
)
def test_and(search_library: Library, query: str, count: int):
    verify_count(search_library, query, count)


@pytest.mark.parametrize(
    ["query", "count"],
    [
        ("square or circle", 17),
        ("orange or green", 10),
        ("orange Or circle", 14),
        ("orange oR square", 14),
        ("square OR green", 14),
        ("circle or green", 14),
        ("green or circle", 14),
        ("filetype:jpg or tag:orange", 11),
        ("red or filetype:png", 28),
        ("filetype:jpg or path:*comp*", 11),
    ],
)
def test_or(search_library: Library, query: str, count: int):
    verify_count(search_library, query, count)


@pytest.mark.parametrize(
    ["query", "count"],
    [
        ("not unexistant", 32),
        ("not path:*", 0),
        ("not not path:*", 32),
        ("not special:untagged", 29),
        ("not filetype:png", 7),
        ("not filetype:jpg", 26),
        ("not tag_id:1011", 27),
        ("not tag_id:1038", 21),
        ("not green", 27),
        ("tag:favorite", 0),
        ("not circle", 21),
        ("not tag:square", 21),
        ("circle and not square", 6),
        ("not circle and square", 6),
        ("special:untagged or not filetype:jpg", 26),
        ("not square or green", 23),
    ],
)
def test_not(search_library: Library, query: str, count: int):
    verify_count(search_library, query, count)


@pytest.mark.parametrize(
    ["query", "count"],
    [
        ("(tag_id:1041)", 11),
        ("(((tag_id:1041)))", 11),
        ("not (not tag_id:1041)", 11),
        ("((circle) and (not square))", 6),
        ("(not ((square) OR (green)))", 18),
        ("filetype:png and (tag:square or green)", 12),
    ],
)
def test_parentheses(search_library: Library, query: str, count: int):
    verify_count(search_library, query, count)


@pytest.mark.parametrize(
    ["query", "count"],
    [
        ("ellipse", 17),
        ("yellow", 15),
        ("color", 25),
        ("shape", 24),
        ("yellow not green", 10),
    ],
)
def test_parent_tags(search_library: Library, query: str, count: int):
    verify_count(search_library, query, count)


@pytest.mark.parametrize(
    "invalid_query", ["asd AND", "asd AND AND", "tag:(", "(asd", "asd[]", "asd]", ":", "tag: :"]
)
def test_syntax(search_library: Library, invalid_query: str):
    with pytest.raises(ParsingError) as e_info:  # noqa: F841  # pyright: ignore[reportUnusedVariable]
        search_library.search_library(BrowsingState.from_search_query(invalid_query), page_size=500)


def _make_size_library(files: list[tuple[str, bytes]]) -> tuple[Library, TemporaryDirectory]:
    """Create a temporary library with files of known sizes.

    Args:
        files: List of (relative path, content) pairs.

    Returns:
        A tuple of (open Library, TemporaryDirectory) — caller must close the tempdir.
    """
    tmp = TemporaryDirectory()
    lib_path = Path(tmp.name)

    lib = Library()
    status = lib.open_library(lib_path)
    assert status.success

    folder = unwrap(lib.folder)
    entries = []
    for rel_path, content in files:
        full = lib_path / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(content)
        entries.append(Entry(folder=folder, path=Path(rel_path), fields=lib.default_fields))

    lib.add_entries(entries)
    return lib, tmp


def test_sort_by_size_ascending():
    """Entries are returned smallest-first when sorting by size ascending."""
    files = [
        ("large.bin", b"x" * 300),
        ("small.bin", b"x" * 100),
        ("medium.bin", b"x" * 200),
    ]
    lib, tmp = _make_size_library(files)
    try:
        state = BrowsingState(sorting_mode=SortingModeEnum.SIZE, ascending=True)
        results = lib.search_library(state, page_size=None)

        assert results.total_count == 3
        sizes = []
        for entry_id in results.ids:
            entry = lib.get_entry(entry_id)
            assert entry is not None
            sizes.append((unwrap(lib.library_dir) / entry.path).stat().st_size)

        assert sizes == sorted(sizes), f"Expected ascending order, got sizes: {sizes}"
    finally:
        tmp.cleanup()


def test_sort_by_size_descending():
    """Entries are returned largest-first when sorting by size descending."""
    files = [
        ("large.bin", b"x" * 300),
        ("small.bin", b"x" * 100),
        ("medium.bin", b"x" * 200),
    ]
    lib, tmp = _make_size_library(files)
    try:
        state = BrowsingState(sorting_mode=SortingModeEnum.SIZE, ascending=False)
        results = lib.search_library(state, page_size=None)

        assert results.total_count == 3
        sizes = []
        for entry_id in results.ids:
            entry = lib.get_entry(entry_id)
            assert entry is not None
            sizes.append((unwrap(lib.library_dir) / entry.path).stat().st_size)

        assert sizes == sorted(sizes, reverse=True), f"Expected descending order, got sizes: {sizes}"
    finally:
        tmp.cleanup()


def test_sort_by_size_empty_result():
    """Sorting an empty result set returns an empty list without error."""
    lib, tmp = _make_size_library([("placeholder.bin", b"x")])
    try:
        state = BrowsingState(
            sorting_mode=SortingModeEnum.SIZE,
            ascending=True,
            query="tag:nonexistent_tag_xyz",
        )
        results = lib.search_library(state, page_size=None)
        assert results.total_count == 0
        assert results.ids == []
    finally:
        tmp.cleanup()


def test_sort_by_size_missing_file_sorts_to_start_ascending():
    """Entries with missing files (size=-1) sort to the start when ascending."""
    files = [
        ("exists.bin", b"x" * 200),
    ]
    lib, tmp = _make_size_library(files)
    try:
        folder = unwrap(lib.folder)
        # Add an entry for a file that doesn't exist on disk
        ghost = Entry(folder=folder, path=Path("ghost.bin"), fields=lib.default_fields)
        lib.add_entries([ghost])

        state = BrowsingState(sorting_mode=SortingModeEnum.SIZE, ascending=True)
        results = lib.search_library(state, page_size=None)

        assert results.total_count == 2
        # The ghost entry (size=-1) should come first in ascending order
        first_entry = lib.get_entry(results.ids[0])
        assert first_entry is not None
        assert first_entry.path == Path("ghost.bin")
    finally:
        tmp.cleanup()
