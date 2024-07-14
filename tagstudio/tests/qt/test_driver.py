from pathlib import Path
from unittest.mock import Mock

from src.core.library import Entry
from src.core.library.json.library import ItemType
from src.qt.widgets.item_thumb import ItemThumb


def test_update_thumbs(qt_driver):
    qt_driver.frame_content = [Entry(path=Path("/tmp/foo"))]

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


def test_select_item_bridge(qt_driver):
    # mock some props since we're not running `start()`
    qt_driver.autofill_action = Mock()
    qt_driver.sort_fields_action = Mock()

    entry = next(qt_driver.lib._entries)

    # set the content manually
    qt_driver.frame_content = [entry] * 3

    qt_driver.filter.page_size = 3
    qt_driver._init_thumb_grid()
    assert len(qt_driver.item_thumbs) == 3

    # select first item
    qt_driver.select_item(0, False, False)
    assert qt_driver.selected == [0]

    # add second item to selection
    qt_driver.select_item(1, False, bridge=True)
    assert qt_driver.selected == [0, 1]

    # add third item to selection
    qt_driver.select_item(2, False, bridge=True)
    assert qt_driver.selected == [0, 1, 2]

    # select third item only
    qt_driver.select_item(2, False, bridge=False)
    assert qt_driver.selected == [2]

    qt_driver.select_item(0, False, bridge=True)
    assert qt_driver.selected == [0, 1, 2]
