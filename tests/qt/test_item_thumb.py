# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import pytest

from tagstudio.core.constants import TAG_FAVORITE
from tagstudio.core.library.alchemy.enums import ItemType
from tagstudio.qt.controllers.item_thumb import ItemThumb
from tagstudio.qt.qt_driver import QtDriver


@pytest.mark.parametrize("new_value", (True, False))
def test_badge_visual_state(qt_driver: QtDriver, entry_min: int, new_value: bool):
    thumb = ItemThumb(
        ItemType.ENTRY, qt_driver.lib, qt_driver, (100, 100), show_filename_label=False
    )

    qt_driver.frame_content = [entry_min]
    qt_driver.selection.toggle_item_selection(0, append=False, bridge=False)

    thumb.layout().badges[TAG_FAVORITE].setChecked(new_value)
    assert thumb.layout().badges[TAG_FAVORITE].isChecked() == new_value
