# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from typing import cast
from unittest.mock import Mock

from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.qt_driver import History, QtDriver


def test_browsing_state_update(qt_driver: QtDriver):
    # Given
    entries = qt_driver.lib.all_entries(with_joins=True)
    ids = [e.id for e in entries]
    qt_driver.frame_content = ids
    qt_driver.main_window.thumb_grid.set_entries(ids)

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


def test_newer_search_replaces_older_one(qt_driver: QtDriver):
    searches: list[Callable[[], None]] = []
    qt_driver.library_pool = Mock()
    qt_driver.library_pool.start.side_effect = searches.append

    qt_driver.update_browsing_state(BrowsingState.from_tag_name("foo"))
    qt_driver.update_browsing_state(BrowsingState.from_path("*bar.md"))
    for search in searches:
        search()

    assert len(qt_driver.frame_content) == 1
    entry = unwrap(qt_driver.lib.get_entry_full(qt_driver.frame_content[0]))
    assert list(entry.tags)[0].name == "bar"


def test_invalid_search_syntax_shows_message(qt_driver: QtDriver):
    qt_driver.update_browsing_state(BrowsingState.from_search_query("tag:("))

    set_results_text = cast(Mock, qt_driver.main_window.set_results_text)
    set_results_text.assert_called_with(f'{Translations["status.results.invalid_syntax"]} "tag:("')


def test_close_library(qt_driver: QtDriver):
    # Given
    qt_driver.close_library()

    # Then
    assert qt_driver.lib.library_dir is None
    assert not qt_driver.frame_content
    assert not qt_driver.selection.selected
    assert len(qt_driver.main_window.thumb_grid._entry_ids) == 0

    # close library again to see there's no error
    qt_driver.close_library()
    qt_driver.close_library(is_shutdown=True)


def test_new_results_start_on_first_page():
    state = BrowsingState(page_index=3, first_visible_entry_id=42)
    new_state = state.with_search_query("tag_id:1000")
    assert new_state.page_index == 0
    assert new_state.first_visible_entry_id is None


def test_history_skips_repeated_states():
    history = History(BrowsingState.from_search_query("foo"))
    history.push(BrowsingState(query="foo", first_visible_entry_id=1))
    history.push(BrowsingState.from_search_query("bar"))

    assert not history.move(1)
    assert history.move(-1)
    assert history.current.query == "foo"
    assert not history.move(-1)
