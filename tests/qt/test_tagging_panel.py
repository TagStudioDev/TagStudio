# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.controllers.tagging_panel import TaggingPanel
from tagstudio.qt.entry_state import EntryState


def test_recent_tags_newest_first(qtbot: QtBot, library: Library, entry_state: EntryState):
    panel = TaggingPanel(library, entry_state)
    qtbot.addWidget(panel)
    first_tag_id, second_tag_id = (tag.id for tag in library.tags[:2])

    panel.add_recent_tags([first_tag_id])
    panel.add_recent_tags([second_tag_id])
    panel.add_recent_tags([first_tag_id])

    assert panel.recent_tags.tag_ids == [first_tag_id, second_tag_id]


def test_recent_tags_leave_out_deleted_tags(
    qtbot: QtBot, library: Library, entry_state: EntryState
):
    panel = TaggingPanel(library, entry_state)
    qtbot.addWidget(panel)
    first_tag_id, second_tag_id = (tag.id for tag in library.tags[-2:])
    panel.add_recent_tags([first_tag_id, second_tag_id])

    library.remove_tag(first_tag_id)

    assert panel.recent_tags.tag_ids == [second_tag_id]
