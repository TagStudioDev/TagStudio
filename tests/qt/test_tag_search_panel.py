# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio
from PySide6.QtCore import SIGNAL
from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.mixed.tag_search import TagSearchPanel
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.ts_qt import QtDriver


def test_update_tags(qtbot: QtBot, library: Library):
    # Given
    panel = TagSearchPanel(library)

    qtbot.addWidget(panel)

    # When
    panel.update_tags()


def test_tag_widget_actions_replaced_correctly(qtbot: QtBot, qt_driver: QtDriver, library: Library):
    panel = TagSearchPanel(library)
    qtbot.addWidget(panel)
    panel.driver = qt_driver

    # Set the widget
    tags = library.tags
    panel.set_tag_widget(tags[0], 0)
    tag_widget: TagWidget = panel.scroll_layout.itemAt(0).widget()

    should_replace_actions = {
        tag_widget: ["on_edit()", "on_remove()"],
        tag_widget.bg_button: ["clicked()"],
        tag_widget.search_for_tag_action: ["triggered()"],
    }

    # Ensure each action has been set
    ensure_one_receiver_per_action(should_replace_actions)

    # Set the widget again
    panel.set_tag_widget(tags[0], 0)

    # Ensure each action has been replaced (amount of receivers is still 1)
    ensure_one_receiver_per_action(should_replace_actions)


def ensure_one_receiver_per_action(should_replace_actions):
    for action, signal_strings in should_replace_actions.items():
        for signal_str in signal_strings:
            assert action.receivers(SIGNAL(signal_str)) == 1
