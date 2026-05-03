# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.qt.controllers.preview_panel_controller import PreviewPanel
from tagstudio.qt.translations import Translations
from tagstudio.qt.ts_qt import QtDriver


def test_update_selection_empty(qt_driver: QtDriver, library: Library):
    panel = PreviewPanel(library, qt_driver)

    # Clear the library selection (selecting 1 then unselecting 1)
    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(1, append=True, bridge=False)
    panel.set_selection(qt_driver.selected)

    # Panel should disable UI that allows for entry modification
    assert not panel.add_buttons_enabled


def test_update_selection_single(qt_driver: QtDriver, library: Library, entry_full: Entry):
    panel = PreviewPanel(library, qt_driver)

    # Select the single entry
    qt_driver.toggle_item_selection(entry_full.id, append=False, bridge=False)
    panel.set_selection(qt_driver.selected)

    # Panel should enable UI that allows for entry modification
    assert panel.add_buttons_enabled


def test_update_selection_multiple(qt_driver: QtDriver, library: Library):
    panel = PreviewPanel(library, qt_driver)

    # Select the multiple entries
    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(2, append=True, bridge=False)
    panel.set_selection(qt_driver.selected)

    # Panel should enable UI that allows for entry modification
    assert panel.add_buttons_enabled

    # File attributes should indicate multiple selection and shared tags
    attrs = panel._file_attributes_widget
    expected_label = Translations.format(
        "preview.multiple_selection", count=len(qt_driver.selected)
    )
    assert attrs.file_label.text() == expected_label


def test_add_field_to_selection_multiple_refreshes(qt_driver: QtDriver, library: Library):
    panel = PreviewPanel(library, qt_driver)

    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(2, append=True, bridge=False)
    panel.set_selection(qt_driver.selected, update_preview=False)

    selected_entries = list(library.get_entries_full([1, 2]))
    existing_field_keys = {field.type_key for entry in selected_entries for field in entry.fields}
    field_type = next(
        value_type
        for value_type in library.field_types.values()
        if value_type.key not in existing_field_keys
    )

    item = QListWidgetItem(f"{field_type.name} ({field_type.type.value})")
    item.setData(Qt.ItemDataRole.UserRole, field_type.key)

    panel._add_field_to_selected([item])

    refreshed_entries = list(library.get_entries_full([1, 2]))
    assert all(
        any(field.type_key == field_type.key for field in entry.fields) for entry in refreshed_entries
    )
    assert all(
        any(field.type_key == field_type.key for field in entry.fields)
        for entry in panel.field_containers_widget.cached_entries
    )
