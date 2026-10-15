# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage=false

from unittest.mock import patch

from tagstudio.core.constants import TAG_FAVORITE
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.inspector import Inspector
from tagstudio.qt.controllers.tiles.tag_data import TagData
from tagstudio.qt.qt_driver import QtDriver


def test_update_selection_empty(qt_driver: QtDriver):
    panel = Inspector(qt_driver)

    # Clear the library selection (selecting 1 then unselecting 1)
    qt_driver.selection.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.selection.toggle_item_selection(1, append=True, bridge=False)

    # Panel should disable UI that allows for entry modification
    assert panel.layout().add_tag_button.isEnabled() == panel.layout().add_field_button.isEnabled()
    assert (
        not panel.layout().add_tag_button.isEnabled()
        and not panel.layout().add_field_button.isEnabled()
    )


def test_update_selection_single(qt_driver: QtDriver, entry_full: Entry):
    panel = Inspector(qt_driver)

    # Select the single entry
    qt_driver.selection.toggle_item_selection(entry_full.id, append=False, bridge=False)

    # Panel should enable UI that allows for entry modification
    assert panel.layout().add_tag_button.isEnabled() == panel.layout().add_field_button.isEnabled()
    assert panel.layout().add_tag_button.isEnabled() and panel.layout().add_field_button.isEnabled()


def test_update_selection_multiple(qt_driver: QtDriver):
    panel = Inspector(qt_driver)

    # Select the multiple entries
    qt_driver.selection.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.selection.toggle_item_selection(2, append=True, bridge=False)

    # Panel should enable UI that allows for entry modification
    assert panel.layout().add_tag_button.isEnabled() == panel.layout().add_field_button.isEnabled()
    assert panel.layout().add_tag_button.isEnabled() and panel.layout().add_field_button.isEnabled()


def test_tag_changes_refresh_once(qt_driver: QtDriver, entry_full: Entry):
    panel = Inspector(qt_driver)
    qt_driver.selection.toggle_item_selection(entry_full.id, append=False, bridge=False)
    containers = panel.containers

    def shown_tag_ids() -> set[int]:
        return {tag.id for tag in containers.cached_entries[0].tags}

    with patch.object(
        containers, "update_from_entry", wraps=containers.update_from_entry
    ) as refresh:
        panel.layout().tag_search_box.item_chosen.emit(2000)
        assert refresh.call_count == 1
        assert shown_tag_ids() == {1000, 2000}
        assert set(panel.layout().tag_search_box.added) == {1000, 2000}

        tag_data = containers._tiles[0].get_inner_widget()
        assert isinstance(tag_data, TagData)
        tag_data._on_remove(unwrap(qt_driver.lib.get_tag(2000)))
        assert refresh.call_count == 2
        assert shown_tag_ids() == {1000}

        qt_driver.entry_state.add_tags(entry_full.id, TAG_FAVORITE)
        assert refresh.call_count == 3
        assert shown_tag_ids() == {1000, TAG_FAVORITE}
