from pathlib import Path
from unittest.mock import Mock

from src.core.library import Entry


def test_update_thumbs(qt_driver):
    qt_driver.frame_content = [Entry(path=Path("/tmp/foo"))]
    qt_driver.update_thumbs()


def test_select_item_bridge(qt_driver):
    # mock some props since we're not running `start()`
    qt_driver.autofill_action = Mock()
    qt_driver.sort_fields_action = Mock()

    entry = qt_driver.lib.entries[0]

    # set the content manually
    qt_driver.frame_content = [entry] * 3

    qt_driver.filter.page_size = 3
    qt_driver._init_thumb_grid()
    assert len(qt_driver.item_thumbs) == 3

    qt_driver.select_item(0, False, False)
    qt_driver.select_item(2, False, True)

    assert qt_driver.selected == [0, 1, 2]
