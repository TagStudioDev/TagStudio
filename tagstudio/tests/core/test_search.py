from pathlib import Path
import src.core.library as lib
from src.core.library import ItemType, Library, Filter, Entry
from src.core.enums import SearchMode
import pytest

# from mock import MagicMock


test_library = Library()
TEST_DIR_PATH = Path.cwd()
lib.TS_FOLDER_NAME = 'mock'
assert test_library.open_library(TEST_DIR_PATH.joinpath('tests/core/mock_library_dir')) == 1



test_entry_one = Entry(id=0, filename='test_file1.png',
                       path='.', fields=[{'6': [1000, 1001]}, {'1': ['James']} ])
test_entry_two = Entry(id=1, filename='test_file2.png',
                       path='test_folder', fields=[{}])
test_entry_three = Entry(id=2, filename='test_file3.png',
                        path='test_folder', fields=[{'6': [1001]},{'4': 'description'}])
test_entry_four = Entry(id=3, filename='test_file3.png',
                        path='test_folder', fields=[{'1': ['Victor']},{'4': 'description'}])

test_library.entries = [test_entry_one, test_entry_two, test_entry_three, test_entry_four]

filter = Filter(test_library)

### CASES ###


decomposition_cases: list[tuple] = [
        ('tag1 tag2',[{'unbound': ['tag1', 'tag2']}]),
        ('tag1 | tag2', [{'unbound': ['tag1']}, {'unbound': ['tag2']}]),
        ('tag1 tag2 | tag3', [{'unbound': ['tag1', 'tag2']}, {'unbound': ['tag3']}]),
        ('tag1; description: desc', [{'unbound': ['tag1'], 'description': 'desc'}])
        ]

remap_cases: list[tuple] = [(test_entry_one, {'tags': [1000, 1001], 'author': ['James']}),
                            (test_entry_two, {}),
                            (test_entry_three, {'tags': [1001], 'description': 'description'}),
                            (test_entry_four, {'author': ['Victor'], 'description': 'description'})

                            ]

filename_cases: list[tuple] = [
        (test_entry_two, '2', True),
        (test_entry_one, '.png', True),
        (test_entry_three, 'test_folder', True),
        (test_entry_one, 'file', True),
        (test_entry_four, None, False)
        ]

populate_tags_cases: list[tuple] = [
        (test_entry_one, ([1000, 1001], ['James'])),
        (test_entry_two, ([], [])),
        (test_entry_three, ([1001], [])),
        (test_entry_four, ([], ['Victor']))
        ]

add_entries_from_special_cases: list[tuple] = [
        (test_entry_one, 'no author', False),
        (test_entry_two, 'empty', True),
        (test_entry_three, 'no author', True),
        (test_entry_four, 'untagged', True)
        ]

filter_case_one: tuple = (
        [{'unbound': 'no author', 'description': 'des'}],
        SearchMode.OR,
        [(ItemType.ENTRY, 2)]
        )
filter_case_two: tuple = (
        [{'unbound': 'notags'}, {'description': 'des'}],
        SearchMode.OR,
        [(ItemType.ENTRY, 1), (ItemType.ENTRY, 2), (ItemType.ENTRY, 3)]
        )
filter_case_three: tuple = (
        [{'tag_id': '1000'}, {'unbound': 'no author'}],
        SearchMode.AND,
        []
        )
filter_case_four: tuple = (
        [{'tag_id': '1001', 'unbound': 'no author'}],
        SearchMode.OR,
        [(ItemType.ENTRY, 2)]
        )

filter_case_five: tuple = (
        [{'tag_id': '1000'}, {'unbound': 'no author'}],
        SearchMode.OR,
        [(ItemType.ENTRY, 0), (ItemType.ENTRY, 1), (ItemType.ENTRY, 2), (ItemType.ENTRY, 3),]
        )

filter_results_cases: list[tuple] = [
        filter_case_one,
        filter_case_two,
        filter_case_three,
        filter_case_four,
        filter_case_five,

        ]

### TESTS ###


@pytest.mark.parametrize("input,expected", decomposition_cases)
def test_query_decomposition(input: str, expected: list[dict]):
    assert test_library.parse_metadata(input) == expected
    pass



@pytest.mark.parametrize("entry,expected", remap_cases)
def test_remap_one(entry: Entry, expected: dict):
    assert filter.remap_fields(entry) == expected


@pytest.mark.parametrize('entry,query,result', filename_cases)
def test_filename(entry: Entry, query: str, result: bool):
    assert filter.check_filename(entry, query) == result

@pytest.mark.parametrize('entry,expected', populate_tags_cases)
def test_populate_tags(entry: Entry, expected: tuple):
    assert filter.populate_tags(entry) == expected
    pass

@pytest.mark.parametrize('entry,unbound_query,expected', add_entries_from_special_cases)
def test_add_entrues_from_special(entry: Entry, unbound_query: str, expected: bool):
    only_no_author: bool = "no author" in unbound_query or "no artist" in unbound_query
    only_untagged: bool = "untagged" in unbound_query or "no tags" in unbound_query
    only_empty: bool = "empty" in unbound_query or "no fields" in unbound_query
    only_missing: bool = "missing" in unbound_query or "no file" in unbound_query
    special_flags = (only_untagged, only_no_author, only_empty, only_missing)
    (entry_tags, entry_authors) = filter.populate_tags(entry)
    result = filter.add_entries_from_special_flags(special_flags, entry_tags,
                                                   entry_authors, entry)
    assert result == expected


@pytest.mark.parametrize('split_query,search_mode,expected', filter_results_cases)
def test_filter_results(split_query: list[dict], search_mode: SearchMode,
                        expected: list[tuple | None]):
    # result_set: set = set()
    # expected_set: set = set()
    assert set(filter.filter_results('', split_query, search_mode)) == set(expected)

