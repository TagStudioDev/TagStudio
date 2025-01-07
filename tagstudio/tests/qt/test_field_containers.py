from src.qt.widgets.preview_panel import PreviewPanel


def test_update_selection_empty(qt_driver, library):
    panel = PreviewPanel(library, qt_driver)

    # Clear the library selection (selecting 1 then unselecting 1)
    qt_driver.select_item(1, append=False, bridge=False)
    qt_driver.select_item(1, append=True, bridge=False)
    panel.update_widgets()

    # FieldContainer should hide all containers
    for container in panel.fields.containers:
        assert container.isHidden()


def test_update_selection_single(qt_driver, library, entry_full):
    panel = PreviewPanel(library, qt_driver)

    # Select the single entry
    qt_driver.select_item(entry_full.id, append=False, bridge=False)
    panel.update_widgets()

    # FieldContainer should show all applicable tags and field containers
    for container in panel.fields.containers:
        assert not container.isHidden()


def test_update_selection_multiple(qt_driver, library):
    # TODO: Implement mixed field editing. Currently these containers will be hidden,
    # same as the empty selection behavior.
    panel = PreviewPanel(library, qt_driver)

    # Select the multiple entries
    qt_driver.select_item(1, append=False, bridge=False)
    qt_driver.select_item(2, append=True, bridge=False)
    panel.update_widgets()

    # FieldContainer should show mixed field editing
    for container in panel.fields.containers:
        assert container.isHidden()


def test_add_tag_to_selection_single(qt_driver, library, entry_full):
    panel = PreviewPanel(library, qt_driver)

    assert {t.id for t in entry_full.tags} == {1000}

    # Select the single entry
    qt_driver.select_item(entry_full.id, append=False, bridge=False)
    panel.update_widgets()

    # Add new tag
    panel.fields.add_tags_to_selected(2000)

    # Then reload entry
    refreshed_entry = next(library.get_entries(with_joins=True))
    assert {t.id for t in refreshed_entry.tags} == {1000, 2000}


def test_add_same_tag_to_selection_single(qt_driver, library, entry_full):
    panel = PreviewPanel(library, qt_driver)

    assert {t.id for t in entry_full.tags} == {1000}

    # Select the single entry
    qt_driver.select_item(entry_full.id, append=False, bridge=False)
    panel.update_widgets()

    # Add an existing tag
    panel.fields.add_tags_to_selected(1000)

    # Then reload entry
    refreshed_entry = next(library.get_entries(with_joins=True))
    assert {t.id for t in refreshed_entry.tags} == {1000}


def test_add_tag_to_selection_multiple(qt_driver, library):
    panel = PreviewPanel(library, qt_driver)
    all_entries = library.get_entries(with_joins=True)

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
    for i, e in enumerate(library.get_entries(with_joins=True), start=0):
        qt_driver.select_item(e.id, append=(True if i == 0 else False), bridge=False)  # noqa: SIM210
    panel.update_widgets()

    # Add new tag
    panel.fields.add_tags_to_selected(1000)

    # Then reload all entries and recheck the presence of tag 1000
    refreshed_entries = library.get_entries(with_joins=True)
    tag_present_on_some: bool = False
    tag_absent_on_some: bool = False

    for e in refreshed_entries:
        if 1000 in [t.id for t in e.tags]:
            tag_present_on_some = True
        else:
            tag_absent_on_some = True

    assert tag_present_on_some
    assert not tag_absent_on_some
