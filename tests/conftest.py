# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import sys
from collections.abc import Callable, Generator
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QScrollArea

CWD = Path(__file__).parent
# this needs to be above `src` imports
sys.path.insert(0, str(CWD.parent))

from tagstudio.core.constants import THUMB_CACHE_NAME, TS_FOLDER_NAME
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry, Tag
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.thumb_grid_layout import ThumbGridLayout
from tagstudio.qt.ts_qt import QtDriver


@pytest.fixture
def cwd():
    return CWD


@pytest.fixture
def file_mediatypes_library():
    lib = Library()

    status = lib.open_library(Path(""), ":memory:")
    assert status.success
    folder = unwrap(lib.folder)

    entry1 = Entry(
        folder=folder,
        path=Path("foo.png"),
        fields=lib.default_fields,
    )

    entry2 = Entry(
        folder=folder,
        path=Path("bar.png"),
        fields=lib.default_fields,
    )

    entry3 = Entry(
        folder=folder,
        path=Path("baz.apng"),
        fields=lib.default_fields,
    )

    assert lib.add_entries([entry1, entry2, entry3])
    assert len(lib.tags) == 3

    return lib


@pytest.fixture(scope="session")
def library_dir():
    """Creates a shared library path for tests, that cleans up after the session."""
    with TemporaryDirectory() as tmp_dir_name:
        library_path = Path(tmp_dir_name)

        thumbs_path = library_path / TS_FOLDER_NAME / THUMB_CACHE_NAME
        thumbs_path.mkdir(parents=True, exist_ok=True)

        yield library_path


@pytest.fixture
def library(request, library_dir: Path):  # pyright: ignore
    # when no param is passed, use the default
    library_path = library_dir
    if hasattr(request, "param"):
        if isinstance(request.param, TemporaryDirectory):
            library_path = Path(request.param.name)  # pyright: ignore[reportArgumentType]
        else:
            library_path = Path(request.param)

    lib = Library()
    status = lib.open_library(library_path, ":memory:")
    assert status.success
    folder = unwrap(lib.folder)

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
        folder=folder,
        path=Path("foo.txt"),
        fields=lib.default_fields,
    )
    assert lib.add_tags_to_entries(entry.id, tag.id)

    entry2 = Entry(
        id=2,
        folder=folder,
        path=Path("one/two/bar.md"),
        fields=lib.default_fields,
    )
    assert lib.add_tags_to_entries(entry2.id, tag2.id)

    assert lib.add_entries([entry, entry2])
    assert len(lib.tags) == 6

    yield lib


@pytest.fixture
def search_library() -> Library:
    lib = Library()
    status = lib.open_library(Path(CWD / "fixtures" / "search_library"))
    assert status.success
    return lib


@pytest.fixture
def entry_min(library: Library):
    yield next(library.all_entries())


@pytest.fixture
def entry_full(library: Library):
    yield next(library.all_entries(with_joins=True))


@pytest.fixture
def qt_driver(library: Library, library_dir: Path):
    class Args:
        settings_file = library_dir / "settings.toml"
        cache_file = library_dir / "tagstudio.ini"
        open = library_dir
        ci = True

    with patch("tagstudio.qt.ts_qt.Consumer"), patch("tagstudio.qt.ts_qt.CustomRunnable"):
        driver = QtDriver(Args())  # pyright: ignore[reportArgumentType]

        driver.app = Mock()
        driver.main_window = Mock()
        driver.main_window.thumb_size = 128
        driver.main_window.thumb_layout = ThumbGridLayout(driver, QScrollArea())
        driver.main_window.menu_bar.autofill_action = Mock()

        driver.copy_buffer = {"fields": [], "tags": []}

        driver.lib = library
        # TODO - downsize this method and use it
        # driver.start()
        driver.frame_content = [e.id for e in library.all_entries()]
        yield driver


@pytest.fixture
def generate_tag() -> Generator[Callable[..., Tag]]:
    def inner(name: str, **kwargs) -> Tag:  # pyright: ignore
        params = dict(name=name, color_namespace="tagstudio-standard", color_slug="red") | kwargs
        return Tag(**params)  # pyright: ignore[reportArgumentType]

    yield inner
