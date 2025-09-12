# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.ts_qt import QtDriver


def test_browsing_state_update(qt_driver: QtDriver):
    # Given
    entries = qt_driver.lib.all_entries(with_joins=True)
    ids = [e.id for e in entries]
    qt_driver.frame_content = ids
    qt_driver.main_window.thumb_layout.set_entries(ids)

    # no filter, both items are returned
    qt_driver.update_browsing_state()
    assert len(qt_driver.frame_content) == 2

    # filter by tag
    state = BrowsingState.from_tag_name("foo")
    qt_driver.update_browsing_state(state)
    assert len(qt_driver.frame_content) == 1
    entry = unwrap(qt_driver.lib.get_entry_full(qt_driver.frame_content[0]))
    assert list(entry.tags)[0].name == "foo"

    # When state is not changed, previous one is still applied
    qt_driver.update_browsing_state()
    assert len(qt_driver.frame_content) == 1
    entry = unwrap(qt_driver.lib.get_entry_full(qt_driver.frame_content[0]))
    assert list(entry.tags)[0].name == "foo"

    # When state property is changed, previous one is overwritten
    state = BrowsingState.from_path("*bar.md")
    qt_driver.update_browsing_state(state)
    assert len(qt_driver.frame_content) == 1
    entry = unwrap(qt_driver.lib.get_entry_full(qt_driver.frame_content[0]))
    assert list(entry.tags)[0].name == "bar"


def test_close_library(qt_driver: QtDriver):
    # Given
    qt_driver.close_library()

    # Then
    assert qt_driver.lib.library_dir is None
    assert not qt_driver.frame_content
    assert not qt_driver.selected
    assert len(qt_driver.main_window.thumb_layout._entry_ids) == 0

    # close library again to see there's no error
    qt_driver.close_library()
    qt_driver.close_library(is_shutdown=True)
