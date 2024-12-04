import pytest
from src.core.library.alchemy.enums import FilterState
from src.core.library.alchemy.library import Library


def verify_count(lib: Library, query: str, count: int):
    results = lib.search_library(FilterState.from_search_query(query))
    assert results.total_count == count
    assert len(results.items) == count


@pytest.mark.parametrize(
    ["query", "count"],
    [
        ("", 29),
        ("path:*", 29),
        ("path:*inherit*", 24),
        ("path:*comp*", 5),
        ("special:untagged", 1),
        ("filetype:png", 23),
        ("filetype:jpg", 6),
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
        ("red or filetype:png", 25),
        ("filetype:jpg or path:*comp*", 11),
    ],
)
def test_or(search_library: Library, query: str, count: int):
    verify_count(search_library, query, count)
