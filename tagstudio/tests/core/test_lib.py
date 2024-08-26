import pytest


def test_open_library(test_library, snapshot_json):
    assert test_library.entries == snapshot_json


@pytest.mark.parametrize(
    ["query"],
    [
        ("First",),
        ("Second",),
        ("--nomatch--",),
    ],
)
def test_library_search(test_library, query, snapshot_json):
    res = test_library.search_library(query)
    assert res == snapshot_json
