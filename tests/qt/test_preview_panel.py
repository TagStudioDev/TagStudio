# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage=false

from tagstudio.core.library.alchemy.models import Entry
from tagstudio.qt.controllers.preview_panel import PreviewPanel
from tagstudio.qt.ts_qt import QtDriver


def test_update_selection_empty(qt_driver: QtDriver):
    panel = PreviewPanel(qt_driver)

    # Clear the library selection (selecting 1 then unselecting 1)
    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(1, append=True, bridge=False)
    panel.set_selection(qt_driver.selected)

    # Panel should disable UI that allows for entry modification
    assert panel._layout.add_tag_button.isEnabled() == panel._layout.add_field_button.isEnabled()
    assert (
        not panel._layout.add_tag_button.isEnabled()
        and not panel._layout.add_field_button.isEnabled()
    )


def test_update_selection_single(qt_driver: QtDriver, entry_full: Entry):
    panel = PreviewPanel(qt_driver)

    # Select the single entry
    qt_driver.toggle_item_selection(entry_full.id, append=False, bridge=False)
    panel.set_selection(qt_driver.selected)

    # Panel should enable UI that allows for entry modification
    assert panel._layout.add_tag_button.isEnabled() == panel._layout.add_field_button.isEnabled()
    assert panel._layout.add_tag_button.isEnabled() and panel._layout.add_field_button.isEnabled()


def test_update_selection_multiple(qt_driver: QtDriver):
    panel = PreviewPanel(qt_driver)

    # Select the multiple entries
    qt_driver.toggle_item_selection(1, append=False, bridge=False)
    qt_driver.toggle_item_selection(2, append=True, bridge=False)
    panel.set_selection(qt_driver.selected)

    # Panel should enable UI that allows for entry modification
    assert panel._layout.add_tag_button.isEnabled() == panel._layout.add_field_button.isEnabled()
    assert panel._layout.add_tag_button.isEnabled() and panel._layout.add_field_button.isEnabled()
