# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage=false


from PySide6.QtCore import QRect
from pytestqt.qtbot import QtBot

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.entry_state import EntryState
from tagstudio.qt.qt_driver import QtDriver


def test_badge_tags_update_state_and_emit(library: Library):
    entry_state = EntryState(library)
    changed: list[set[int]] = []
    entry_state.tags_changed.connect(changed.append)

    entry_state.add_tags([1, 2], TAG_FAVORITE)
    assert entry_state.has_badge(1, TAG_FAVORITE)
    assert entry_state.has_badge(2, TAG_FAVORITE)
    assert library.get_tag_entries([TAG_FAVORITE], [1, 2])[TAG_FAVORITE] == {1, 2}
    assert changed == [{1, 2}]

    entry_state.remove_tags(2, TAG_FAVORITE)
    assert entry_state.has_badge(1, TAG_FAVORITE)
    assert not entry_state.has_badge(2, TAG_FAVORITE)
    assert changed[-1] == {2}


def test_non_badge_tags_emit(library: Library):
    entry_state = EntryState(library)
    changed: list[set[int]] = []
    entry_state.tags_changed.connect(changed.append)

    non_badge_tag = 2000
    entry_state.add_tags(1, non_badge_tag)
    assert changed == [{1}]


def test_unload_badges_rereads_from_library(library: Library):
    entry_state = EntryState(library)
    library.add_tags_to_entries(1, TAG_ARCHIVED)
    entry_state.unload_badges()
    assert entry_state.has_badge(1, TAG_ARCHIVED)


def test_badge_click_updates_whole_selection(qt_driver: QtDriver, qtbot: QtBot):
    grid = qt_driver.main_window.thumb_grid
    grid.set_entries([1, 2])
    grid.layout().setGeometry(QRect(0, 0, 1000, 1000))
    qtbot.waitUntil(lambda: not grid._held)
    thumbs = [unwrap(grid.layout().widget_at(index)) for index in (0, 1)]

    qt_driver.selection.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.selection.toggle_item_selection(2, append=True, bridge=False)
    thumbs[0].layout().badges[TAG_FAVORITE].setChecked(True)

    assert all(thumb.layout().badges[TAG_FAVORITE].isChecked() for thumb in thumbs)
    assert qt_driver.lib.get_tag_entries([TAG_FAVORITE], [1, 2])[TAG_FAVORITE] == {1, 2}
