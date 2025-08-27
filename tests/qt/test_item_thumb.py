# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import pytest

from tagstudio.core.library.alchemy.enums import ItemType
from tagstudio.qt.ts_qt import QtDriver
from tagstudio.qt.widgets.item_thumb import BadgeType, ItemThumb


@pytest.mark.parametrize("new_value", (True, False))
def test_badge_visual_state(qt_driver: QtDriver, entry_min: int, new_value: bool):
    thumb = ItemThumb(
        ItemType.ENTRY, qt_driver.lib, qt_driver, (100, 100), show_filename_label=False
    )

    qt_driver.frame_content = [entry_min]
    qt_driver.selected = [0]
    qt_driver.item_thumbs = [thumb]

    thumb.badges[BadgeType.FAVORITE].setChecked(new_value)
    assert thumb.badges[BadgeType.FAVORITE].isChecked() == new_value
    # TODO
    # assert thumb.favorite_badge.isHidden() == initial_state
    assert thumb.is_favorite == new_value
