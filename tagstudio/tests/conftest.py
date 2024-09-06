import sys
import pathlib
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock

import pytest

CWD = pathlib.Path(__file__).parent
# this needs to be above `src` imports
sys.path.insert(0, str(CWD.parent))

from src.core.library import Library, Tag
from src.core.library.alchemy.enums import TagColor
from src.core.library.alchemy.fields import TagBoxField, _FieldID
from tests.test_library import generate_entry
from src.core.library import alchemy as backend
from src.qt.ts_qt import QtDriver


@pytest.fixture
def cwd():
    return CWD


@pytest.fixture
def library(request):
    # when no param is passed, use the default
    library_path = "/tmp/"
    if hasattr(request, "param"):
        if isinstance(request.param, TemporaryDirectory):
            library_path = request.param.name
        else:
            library_path = request.param

    lib = Library()
    lib.open_library(library_path, ":memory:")

    tag = Tag(
        name="foo",
        color=TagColor.RED,
    )

    tag2 = Tag(
        name="bar",
        color=TagColor.BLUE,
    )

    assert lib.add_tag(tag)

    # default item with deterministic name
    entry = generate_entry(path=pathlib.Path("foo.txt"))

    entry.tag_box_fields = [
        TagBoxField(
            type_key=_FieldID.TAGS.name,
            tags={tag},
        ),
        TagBoxField(
            type_key=_FieldID.TAGS_META.name,
            # tags={tag2}
        ),
    ]

    entry2 = generate_entry(path=pathlib.Path("one/two/bar.md"))
    entry2.tag_box_fields = [
        TagBoxField(
            tags={tag2},
            type_key=_FieldID.TAGS_META.name,
        ),
    ]

    assert lib.add_entries([entry, entry2])
    assert len(lib.tags) == 4

    yield lib


@pytest.fixture
def entry_min(library):
    yield next(library.get_entries())


@pytest.fixture
def entry_full(library):
    yield next(library.get_entries(with_joins=True))


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
            # TODO - downsize this method and use it
            # driver.start()
            driver.frame_content = list(library.get_entries())
            yield driver


@pytest.fixture
def generate_tag():
    def inner(name, **kwargs):
        params = dict(name=name, color=TagColor.RED) | kwargs
        return Tag(**params)

    yield inner
