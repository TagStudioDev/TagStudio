from pathlib import Path
import src.core.library as lib
from src.core.library import Library, Filter, Entry
import pytest
from mock import MagicMock


test_library = Library()
TEST_DIR_PATH = Path.cwd()
lib.TS_FOLDER_NAME = 'mock'
assert test_library.open_library(TEST_DIR_PATH.joinpath('tests/core/mock_library_dir')) == 1
test_library._

filter = Filter(test_library)

### TESTS ###

decomposition_cases: list[tuple] = [
        ('tag1 tag2',[{'unbound': ['tag1', 'tag2']}]),
        ('tag1 | tag2', [{'unbound': ['tag1']}, {'unbound': ['tag2']}]),
        ('tag1 tag2 | tag3', [{'unbound': ['tag1', 'tag2']}, {'unbound': ['tag3']}]),
        ('tag1; description: desc', [{'unbound': ['tag1'], 'description': 'desc'}])
        ]

@pytest.mark.parametrize("input,expected", decomposition_cases)
def test_query_decomposition(input: str, expected: list[dict]):
    assert test_library.parse_metadata(input) == expected
    pass


test_entry_one = Entry(id=0, filename='test_file1.png',
                       path='.', fields=[{'6': [1000, 1001]}])
test_entry_two = Entry(id=1, filename='test_file2.png',
                       path='test_folder', fields=[{}])
test_entry_tree = Entry(id=2, filename='test_file3.png',
                        path='test_folder', fields=[{'6': [1001]},{'4': 'description'}])
remap_cases: list[tuple] = [(test_entry_one, {'tags': [1000, 1001]}),
                            (test_entry_two, {}),
                            (test_entry_tree, {'tags': [1001], 'description': 'description'})]

@pytest.mark.parametrize("entry,expected", remap_cases)
def test_remap_one(entry: Entry, expected: dict):
    filter._field_id_to_name_map = {'6': 'tags', '4': 'description'}
    assert filter.remap_fields(entry) == expected


def test_filename(entry):
    pass


