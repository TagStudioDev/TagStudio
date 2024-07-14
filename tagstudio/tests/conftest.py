import sys
import pathlib
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock

import pytest
from syrupy.extensions.json import JSONSnapshotExtension

CWD = pathlib.Path(__file__).parent
# this needs to be above `src` imports
sys.path.insert(0, str(CWD.parent))

from src.core.library import Library, Tag
from src.core.library.alchemy.enums import TagColor
from src.core.library.alchemy.fields import TagBoxField
from tests.alchemy.test_library import generate_entry
from src.core.library import alchemy as backend
from src.qt.ts_qt import QtDriver


@pytest.fixture
def snapshot_json(snapshot):
    return snapshot.with_defaults(extension_class=JSONSnapshotExtension)


@pytest.fixture
def library():
    # reset generated entries
    lib = Library()
    lib.open_library(":memory:")

    tag = Tag(
        name="foo",
        color=TagColor.red,
    )

    assert lib.add_tag(tag)

    # default item with deterministic name
    entry = generate_entry(path=pathlib.Path("foo.txt"))
    entry.tag_box_fields = [
        TagBoxField(
            name="tag_box",
            tags={tag},
        ),
    ]

    assert lib.add_entries([entry])
    assert lib.tags

    yield lib


@pytest.fixture
def qt_driver(qtbot, library):
    with TemporaryDirectory() as tmp_dir:

        class Args:
            config_file = pathlib.Path(tmp_dir) / "tagstudio.ini"
            open = pathlib.Path(tmp_dir)
            ci = True

        # patch CustomRunnable

        with patch("src.qt.ts_qt.Consumer"), patch("src.qt.ts_qt.CustomRunnable"):
            driver = QtDriver(backend, Args())

            driver.main_window = Mock()
            driver.preview_panel = Mock()
            driver.flow_container = Mock()
            driver.item_thumbs = []

            driver.lib = library
            # driver.start()
            # driver.open_library(":memory:")
            # driver.lib.add_entries([generate_entry(path=pathlib.Path("foo.txt"))])
            driver.frame_content = library.entries
            yield driver
