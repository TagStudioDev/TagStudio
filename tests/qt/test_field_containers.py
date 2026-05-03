# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry, Tag
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.controllers.preview_panel_controller import PreviewPanel
from tagstudio.qt.translations import Translations
from tagstudio.qt.ts_qt import QtDriver


def test_update_selection_empty(qt_driver: QtDriver, library: Library):
    panel = PreviewPanel(library, qt_driver)

    # Clear the library selection (selecting 1 then unselecting 1)
    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(1, append=True, bridge=False)
    panel.set_selection(qt_driver.selected)

    # FieldContainer should hide all containers
    for container in panel.field_containers_widget.containers:
        assert container.isHidden()


def test_update_selection_single(qt_driver: QtDriver, library: Library, entry_full: Entry):
    panel = PreviewPanel(library, qt_driver)

    # Select the single entry
    qt_driver.toggle_item_selection(entry_full.id, append=False, bridge=False)
    panel.set_selection(qt_driver.selected)

    # FieldContainer should show all applicable tags and field containers
    for container in panel.field_containers_widget.containers:
        assert not container.isHidden()


def test_update_selection_multiple(qt_driver: QtDriver, library: Library):
    panel = PreviewPanel(library, qt_driver)

    # Select the multiple entries
    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(2, append=True, bridge=False)
    panel.set_selection(qt_driver.selected)

    # Panel should enable UI that allows for entry modification and cache all selected entries
    assert panel.add_buttons_enabled
    assert len(panel.field_containers_widget.cached_entries) == 2


def test_add_tag_to_selection_single(qt_driver: QtDriver, library: Library, entry_full: Entry):
    panel = PreviewPanel(library, qt_driver)

    assert {t.id for t in entry_full.tags} == {1000}

    # Select the single entry
    qt_driver.toggle_item_selection(entry_full.id, append=False, bridge=False)
    panel.set_selection(qt_driver.selected)

    # Add new tag
    panel.field_containers_widget.add_tags_to_selected(2000)

    # Then reload entry
    refreshed_entry: Entry = next(library.all_entries(with_joins=True))
    assert {t.id for t in refreshed_entry.tags} == {1000, 2000}


def test_add_same_tag_to_selection_single(qt_driver: QtDriver, library: Library, entry_full: Entry):
    panel = PreviewPanel(library, qt_driver)

    assert {t.id for t in entry_full.tags} == {1000}

    # Select the single entry
    qt_driver.toggle_item_selection(entry_full.id, append=False, bridge=False)
    panel.set_selection(qt_driver.selected)

    # Add an existing tag
    panel.field_containers_widget.add_tags_to_selected(1000)

    # Then reload entry
    refreshed_entry = next(library.all_entries(with_joins=True))
    assert {t.id for t in refreshed_entry.tags} == {1000}


def test_add_tag_to_selection_multiple(qt_driver: QtDriver, library: Library):
    panel = PreviewPanel(library, qt_driver)
    all_entries = library.all_entries(with_joins=True)

    # We want to verify that tag 1000 is on some, but not all entries already.
    tag_present_on_some: bool = False
    tag_absent_on_some: bool = False

    for e in all_entries:
        if 1000 in [t.id for t in e.tags]:
            tag_present_on_some = True
        else:
            tag_absent_on_some = True

    assert tag_present_on_some
    assert tag_absent_on_some

    # Select the multiple entries
    for i, e in enumerate(library.all_entries(with_joins=True), start=0):
        qt_driver.toggle_item_selection(e.id, append=(True if i == 0 else False), bridge=False)  # noqa: SIM210
    panel.set_selection(qt_driver.selected)

    # Add new tag
    panel.field_containers_widget.add_tags_to_selected(1000)

    # Then reload all entries and recheck the presence of tag 1000
    refreshed_entries = library.all_entries(with_joins=True)
    tag_present_on_some = False
    tag_absent_on_some = False

    for e in refreshed_entries:
        if 1000 in [t.id for t in e.tags]:
            tag_present_on_some = True
        else:
            tag_absent_on_some = True

    assert tag_present_on_some
    assert not tag_absent_on_some


def test_meta_tag_category(qt_driver: QtDriver, library: Library, entry_full: Entry):
    panel = PreviewPanel(library, qt_driver)

    # Ensure the Favorite tag is on entry_full
    library.add_tags_to_entries(1, entry_full.id)

    # Select the single entry
    qt_driver.toggle_item_selection(entry_full.id, append=False, bridge=False)
    panel.set_selection(qt_driver.selected)

    # FieldContainer should hide all containers
    assert len(panel.field_containers_widget.containers) == 3
    for i, container in enumerate(panel.field_containers_widget.containers):
        match i:
            case 0:
                # Check if the container is the Meta Tags category
                tag: Tag = unwrap(library.get_tag(2))
                assert container.title == f"<h4>{tag.name}</h4>"
            case 1:
                # Check if the container is the Tags category
                assert container.title == "<h4>Tags</h4>"
            case 2:
                # Make sure the container isn't a duplicate Tags category
                assert container.title != "<h4>Tags</h4>"
            case _:
                pass


def test_custom_tag_category(qt_driver: QtDriver, library: Library, entry_full: Entry):
    panel = PreviewPanel(library, qt_driver)

    # Set tag 1000 (foo) as a category
    tag: Tag = unwrap(library.get_tag(1000))
    tag.is_category = True
    library.update_tag(
        tag,
    )

    # Ensure the Favorite tag is on entry_full
    library.add_tags_to_entries(1, entry_full.id)

    # Select the single entry
    qt_driver.toggle_item_selection(entry_full.id, append=False, bridge=False)
    panel.set_selection(qt_driver.selected)

    # FieldContainer should hide all containers
    assert len(panel.field_containers_widget.containers) == 3
    for i, container in enumerate(panel.field_containers_widget.containers):
        match i:
            case 0:
                # Check if the container is the Meta Tags category
                tag_2: Tag = unwrap(library.get_tag(2))
                assert container.title == f"<h4>{tag_2.name}</h4>"
            case 1:
                # Check if the container is the custom "foo" category
                assert container.title == f"<h4>{tag.name}</h4>"
            case 2:
                # Make sure the container isn't a plain Tags category
                assert container.title != "<h4>Tags</h4>"
            case _:
                pass


def test_multi_selection_mixed_section_resets_on_single_selection(
    qt_driver: QtDriver, library: Library
):
    panel = PreviewPanel(library, qt_driver)
    field_containers = panel.field_containers_widget

    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(2, append=True, bridge=False)
    panel.set_selection(qt_driver.selected)

    container_titles = [c.title for c in field_containers.containers]
    assert f"<h4>{Translations['preview.partial_section']}</h4>" in container_titles
    assert "<h4>Tags</h4>" in container_titles
    assert "<h4>Title</h4>" in container_titles
    assert [entry.id for entry in field_containers.cached_entries] == [1, 2]

    # Switch back to single selection — the partial section should disappear
    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    panel.set_selection(qt_driver.selected)

    entry = unwrap(library.get_entry_full(1))
    active_container_count = len(field_containers.get_tag_categories(entry.tags)) + len(entry.fields)
    active_titles = [field_containers.containers[i].title for i in range(active_container_count)]
    assert f"<h4>{Translations['preview.partial_section']}</h4>" not in active_titles
    assert [cached_entry.id for cached_entry in field_containers.cached_entries] == [1]
