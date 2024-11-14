import pathlib
import sys
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest

CWD = pathlib.Path(__file__).parent
# this needs to be above `src` imports
sys.path.insert(0, str(CWD.parent))

from src.core.library import Entry, Library, Tag
from src.core.library import alchemy as backend
from src.core.library.alchemy.enums import TagColor
from src.core.library.alchemy.fields import TagBoxField, _FieldID
from src.qt.ts_qt import QtDriver


@pytest.fixture
def cwd():
    return CWD


@pytest.fixture
def file_mediatypes_library():
    lib = Library()

    status = lib.open_library(pathlib.Path(""), ":memory:")
    assert status.success

    entry1 = Entry(
        folder=lib.folder,
        path=pathlib.Path("foo.png"),
        fields=lib.default_fields,
    )

    entry2 = Entry(
        folder=lib.folder,
        path=pathlib.Path("bar.png"),
        fields=lib.default_fields,
    )

    entry3 = Entry(
        folder=lib.folder,
        path=pathlib.Path("baz.apng"),
        fields=lib.default_fields,
    )

    assert lib.add_entries([entry1, entry2, entry3])
    assert len(lib.tags) == 2

    return lib


@pytest.fixture
def library(request):
    # when no param is passed, use the default
    library_path = "/dev/null/"
    if hasattr(request, "param"):
        if isinstance(request.param, TemporaryDirectory):
            library_path = request.param.name
        else:
            library_path = request.param

    lib = Library()
    status = lib.open_library(pathlib.Path(library_path), ":memory:")
    assert status.success

    tag = Tag(
        name="foo",
        color=TagColor.RED,
    )
    assert lib.add_tag(tag)

    subtag = Tag(
        name="subbar",
        color=TagColor.YELLOW,
    )

    tag2 = Tag(
        name="bar",
        color=TagColor.BLUE,
        subtags={subtag},
    )

    # default item with deterministic name
    entry = Entry(
        folder=lib.folder,
        path=pathlib.Path("foo.txt"),
        fields=lib.default_fields,
    )

    entry.tag_box_fields = [
        TagBoxField(type_key=_FieldID.TAGS.name, tags={tag}, position=0),
        TagBoxField(
            type_key=_FieldID.TAGS_META.name,
            position=0,
        ),
    ]

    entry2 = Entry(
        folder=lib.folder,
        path=pathlib.Path("one/two/bar.md"),
        fields=lib.default_fields,
    )
    entry2.tag_box_fields = [
        TagBoxField(
            tags={tag2},
            type_key=_FieldID.TAGS_META.name,
            position=0,
        ),
    ]

    assert lib.add_entries([entry, entry2])
    assert len(lib.tags) == 5

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
