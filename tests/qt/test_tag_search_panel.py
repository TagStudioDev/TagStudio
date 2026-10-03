# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import SIGNAL
from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.tag_search_panel import TagSearchPanel
from tagstudio.qt.views.search_panel_view import SearchPanelView


def test_update_tags(qtbot: QtBot, library: Library):
    # Given
    panel = TagSearchPanel(library, view=SearchPanelView("", is_chooser=True))

    qtbot.addWidget(panel)

    # When
    panel.update_items()


def test_removed_tag_capsules_hidden(qtbot: QtBot, library: Library):
    """Regression test for #1523."""
    panel = TagSearchPanel(library, is_chooser=False)
    qtbot.addWidget(panel)

    # 1. Set view limit to "All Items"
    panel.set_limit_index(panel.layout().limit_combobox.count() - 1)
    panel.update_items()

    # 2. Delete a tag
    library.remove_tag(library.tags[-1].id)
    panel.update_items()

    # 3. Assert that there's the correct number of visible capsules and no duplicates
    visible_capsules = [
        i
        for i in range(panel.layout().scroll_layout.count())
        if not panel.get_item_widget(i, library).isHidden()
    ]
    assert len(visible_capsules) == len(library.tags)


def test_capsule_actions_replaced_correctly(qtbot: QtBot, library: Library):
    panel = TagSearchPanel(library, view=SearchPanelView(""))
    qtbot.addWidget(panel)

    # Set the widget
    tags = library.tags
    panel.set_item_widget(tags[0], 0)
    capsule: Capsule = panel.get_item_widget(0, library)

    should_replace_actions = {
        capsule: ["on_click()", "on_edit()", "on_remove()", "on_search()"],
    }

    # Ensure each action has been set
    ensure_one_receiver_per_action(should_replace_actions)

    # Set the widget again
    panel.set_item_widget(tags[0], 0)

    # Ensure each action has been replaced (amount of receivers is still 1)
    ensure_one_receiver_per_action(should_replace_actions)


def ensure_one_receiver_per_action(should_replace_actions):
    for action, signal_strings in should_replace_actions.items():
        for signal_str in signal_strings:
            assert action.receivers(SIGNAL(signal_str)) == 1
