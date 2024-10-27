from pathlib import Path
from unittest.mock import Mock

from src.core.library import Entry
from src.core.library.alchemy.enums import FilterState
from src.core.library.json.library import ItemType
from src.qt.widgets.item_thumb import ItemThumb


def test_update_thumbs(qt_driver):
    qt_driver.frame_content = [
        Entry(
            folder=qt_driver.lib.folder,
            path=Path("/tmp/foo"),
            fields=qt_driver.lib.default_fields,
        )
    ]

    qt_driver.item_thumbs = []
    for i in range(3):
        qt_driver.item_thumbs.append(
            ItemThumb(
                mode=ItemType.ENTRY,
                library=qt_driver.lib,
                driver=qt_driver,
                thumb_size=(100, 100),
                grid_idx=i,
            )
        )

    qt_driver.update_thumbs()

    for idx, thumb in enumerate(qt_driver.item_thumbs):
        # only first item is visible
        assert thumb.isVisible() == (idx == 0)


def test_select_item_bridge(qt_driver, entry_min):
    # mock some props since we're not running `start()`
    qt_driver.autofill_action = Mock()
    qt_driver.sort_fields_action = Mock()

    # set the content manually
    qt_driver.frame_content = [entry_min] * 3

    qt_driver.filter.page_size = 3
    qt_driver._init_thumb_grid()
    assert len(qt_driver.item_thumbs) == 3

    # select first item
    qt_driver.select_item(0, append=False, bridge=False)
    assert qt_driver.selected == [0]

    # add second item to selection
    qt_driver.select_item(1, append=False, bridge=True)
    assert qt_driver.selected == [0, 1]

    # add third item to selection
    qt_driver.select_item(2, append=False, bridge=True)
    assert qt_driver.selected == [0, 1, 2]

    # select third item only
    qt_driver.select_item(2, append=False, bridge=False)
    assert qt_driver.selected == [2]

    qt_driver.select_item(0, append=False, bridge=True)
    assert qt_driver.selected == [0, 1, 2]


def test_library_state_update(qt_driver):
    # Given
    for idx, entry in enumerate(qt_driver.lib.get_entries(with_joins=True)):
        thumb = ItemThumb(ItemType.ENTRY, qt_driver.lib, qt_driver, (100, 100), idx)
        qt_driver.item_thumbs.append(thumb)
        qt_driver.frame_content.append(entry)

    # no filter, both items are returned
    qt_driver.filter_items()
    assert len(qt_driver.frame_content) == 2

    # filter by tag
    state = FilterState(tag="foo", page_size=10)
    qt_driver.filter_items(state)
    assert qt_driver.filter.page_size == 10
    assert len(qt_driver.frame_content) == 1
    entry = qt_driver.frame_content[0]
    assert list(entry.tags)[0].name == "foo"

    # When state is not changed, previous one is still applied
    qt_driver.filter_items()
    assert qt_driver.filter.page_size == 10
    assert len(qt_driver.frame_content) == 1
    entry = qt_driver.frame_content[0]
    assert list(entry.tags)[0].name == "foo"

    # When state property is changed, previous one is overwritten
    state = FilterState(path="bar.md")
    qt_driver.filter_items(state)
    assert len(qt_driver.frame_content) == 1
    entry = qt_driver.frame_content[0]
    assert list(entry.tags)[0].name == "bar"


def test_close_library(qt_driver):
    # Given
    qt_driver.close_library()

    # Then
    assert qt_driver.lib.library_dir is None
    assert not qt_driver.frame_content
    assert not qt_driver.selected
    assert not any(x.mode for x in qt_driver.item_thumbs)

    # close library again to see there's no error
    qt_driver.close_library()
    qt_driver.close_library(is_shutdown=True)
