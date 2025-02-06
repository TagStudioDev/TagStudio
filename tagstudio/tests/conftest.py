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
    assert len(lib.tags) == 3

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
        color_namespace="tagstudio-standard",
        color_slug="red",
    )
    assert lib.add_tag(tag)

    parent_tag = Tag(
        id=1500,
        name="subbar",
        color_namespace="tagstudio-standard",
        color_slug="yellow",
    )
    assert lib.add_tag(parent_tag)

    tag2 = Tag(
        id=2000,
        name="bar",
        color_namespace="tagstudio-standard",
        color_slug="blue",
        parent_tags={parent_tag},
    )
    assert lib.add_tag(tag2)

    # default item with deterministic name
    entry = Entry(
        id=1,
        folder=lib.folder,
        path=pathlib.Path("foo.txt"),
        fields=lib.default_fields,
    )
    assert lib.add_tags_to_entries(entry.id, tag.id)

    entry2 = Entry(
        id=2,
        folder=lib.folder,
        path=pathlib.Path("one/two/bar.md"),
        fields=lib.default_fields,
    )
    assert lib.add_tags_to_entries(entry2.id, tag2.id)

    assert lib.add_entries([entry, entry2])
    assert len(lib.tags) == 6

    yield lib


@pytest.fixture
def search_library() -> Library:
    lib = Library()
    lib.open_library(pathlib.Path(CWD / "fixtures" / "search_library"))
    return lib


@pytest.fixture
def entry_min(library):
    yield next(library.get_entries())


@pytest.fixture
def entry_full(library: Library):
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
            driver.autofill_action = Mock()

            driver.copy_buffer = {"fields": [], "tags": []}
            driver.copy_fields_action = Mock()
            driver.paste_fields_action = Mock()

            driver.lib = library
            # TODO - downsize this method and use it
            # driver.start()
            driver.frame_content = list(library.get_entries())
            yield driver


@pytest.fixture
def generate_tag():
    def inner(name, **kwargs):
        params = dict(name=name, color_namespace="tagstudio-standard", color_slug="red") | kwargs
        return Tag(**params)

    yield inner
