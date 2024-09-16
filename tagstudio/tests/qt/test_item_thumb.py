import pytest
from src.core.library import ItemType
from src.qt.widgets.item_thumb import BadgeType, ItemThumb


@pytest.mark.parametrize("new_value", (True, False))
def test_badge_visual_state(library, qt_driver, entry_min, new_value):
    thumb = ItemThumb(ItemType.ENTRY, qt_driver.lib, qt_driver, (100, 100), 0)

    qt_driver.frame_content = [entry_min]
    qt_driver.selected = [0]
    qt_driver.item_thumbs = [thumb]

    thumb.badges[BadgeType.FAVORITE].setChecked(new_value)
    assert thumb.badges[BadgeType.FAVORITE].isChecked() == new_value
    # TODO
    # assert thumb.favorite_badge.isHidden() == initial_state
    assert thumb.is_favorite == new_value
