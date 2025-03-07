from src.qt.widgets.preview_panel import PreviewPanel


def test_update_selection_empty(qt_driver, library):
    panel = PreviewPanel(library, qt_driver)

    # Clear the library selection (selecting 1 then unselecting 1)
    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(1, append=True, bridge=False)
    panel.update_widgets()

    # Panel should disable UI that allows for entry modification
    assert not panel.add_tag_button.isEnabled()
    assert not panel.add_field_button.isEnabled()


def test_update_selection_single(qt_driver, library, entry_full):
    panel = PreviewPanel(library, qt_driver)

    # Select the single entry
    qt_driver.toggle_item_selection(entry_full.id, append=False, bridge=False)
    panel.update_widgets()

    # Panel should enable UI that allows for entry modification
    assert panel.add_tag_button.isEnabled()
    assert panel.add_field_button.isEnabled()


def test_update_selection_multiple(qt_driver, library):
    panel = PreviewPanel(library, qt_driver)

    # Select the multiple entries
    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(2, append=True, bridge=False)
    panel.update_widgets()

    # Panel should enable UI that allows for entry modification
    assert panel.add_tag_button.isEnabled()
    assert panel.add_field_button.isEnabled()
