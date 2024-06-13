import sys
import pathlib

import pytest
from syrupy.extensions.json import JSONSnapshotExtension

CWD = pathlib.Path(__file__).parent

sys.path.insert(0, str(CWD.parent))

from src.core.library import Tag, Library


@pytest.fixture
def test_tag():
    yield Tag(
        id=1,
        name="Tag Name",
        shorthand="TN",
        aliases=["First A", "Second A"],
        subtags_ids=[2, 3, 4],
        color="",
    )


@pytest.fixture
def test_library():
    lib = Library()
    ret_code = lib.open_library(CWD / "fixtures" / "library")
    assert ret_code == 1
    yield lib


@pytest.fixture
def snapshot_json(snapshot):
    return snapshot.with_defaults(extension_class=JSONSnapshotExtension)
