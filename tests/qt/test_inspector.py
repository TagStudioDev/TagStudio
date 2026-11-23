# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage=false

from unittest.mock import Mock

from tagstudio.core.constants import TAG_FAVORITE
from tagstudio.core.library.alchemy.models import Entry, Tag
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.inspector import Inspector
from tagstudio.qt.controllers.tiles.tag_data import TagData
from tagstudio.qt.qt_driver import QtDriver


def category_names(panel: Inspector, tag_id: int) -> dict[str | None, set[str]]:
    cached_tag = unwrap(panel.containers.lib.get_cached_tag(tag_id))
    categories = panel.containers.get_tag_categories([cached_tag])
    return {
        category.name if category else None: {tag.name for tag in tags}
        for category, tags in categories.items()
    }


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


def test_tag_changes_refresh_shown_tags(qt_driver: QtDriver, entry_full: Entry):
    panel = Inspector(qt_driver)
    qt_driver.selection.toggle_item_selection(entry_full.id, append=False, bridge=False)
    containers = panel.containers

    def shown_tag_ids() -> set[int]:
        return {tag.id for tag in containers.cached_entries[0].tags}

    panel.layout().tag_search_box.item_chosen.emit(2000)
    assert shown_tag_ids() == {1000, 2000}
    assert set(panel.layout().tag_search_box.added) == {1000, 2000}

    tag_data = containers._tiles[0].get_inner_widget()
    assert isinstance(tag_data, TagData)
    tag_data._on_remove(unwrap(qt_driver.lib.get_cached_tag(2000)))
    assert shown_tag_ids() == {1000}

    qt_driver.entry_state.add_tags(entry_full.id, TAG_FAVORITE)
    assert shown_tag_ids() == {1000, TAG_FAVORITE}


def test_reloading_an_unchanged_entry_does_not_redraw(qt_driver: QtDriver, entry_full: Entry):
    panel = Inspector(qt_driver)
    qt_driver.selection.toggle_item_selection(entry_full.id, append=False, bridge=False)
    shown_contents = panel.containers._shown_contents

    panel.containers.update_from_entry(entry_full.id)

    assert panel.containers._shown_contents is shown_contents


def test_finished_tag_writes_show_before_the_entry_reloads(qt_driver: QtDriver, entry_full: Entry):
    panel = Inspector(qt_driver)
    qt_driver.selection.toggle_item_selection(entry_full.id, append=False, bridge=False)
    panel.containers._load_pool = Mock()  # Never runs the reloads

    panel.layout().tag_search_box.item_chosen.emit(2000)

    assert set(panel.containers.tags) == {1000, 2000}


def test_tags_show_under_category_ancestors(qt_driver: QtDriver):
    lib = qt_driver.lib
    category = unwrap(lib.add_tag(Tag(name="Character", is_category=True)))
    parent = unwrap(lib.add_tag(Tag(name="Cartoon"), parent_ids={category.id}))
    tag = unwrap(lib.add_tag(Tag(name="Jonathan"), parent_ids={parent.id}))

    assert category_names(Inspector(qt_driver), tag.id) == {"Character": {"Jonathan"}}


def test_tags_skip_excluded_categories(qt_driver: QtDriver):
    lib = qt_driver.lib
    category = unwrap(lib.add_tag(Tag(name="Character", is_category=True)))
    tag = unwrap(
        lib.add_tag(Tag(name="Jonathan"), parent_ids={category.id}, exclusion_ids={category.id})
    )

    assert category_names(Inspector(qt_driver), tag.id) == {None: {"Jonathan"}}
