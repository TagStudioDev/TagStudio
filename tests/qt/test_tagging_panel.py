# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from tempfile import TemporaryDirectory

import pytest
from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.controllers.tagging_panel import TaggingPanel
from tagstudio.qt.entry_state import EntryState
from tagstudio.qt.pinned_tags_state import PinnedTagsState


def test_recent_tags_newest_first(
    qtbot: QtBot, library: Library, entry_state: EntryState, pinned_tags_state: PinnedTagsState
):
    panel = TaggingPanel(library, entry_state, pinned_tags_state)
    qtbot.addWidget(panel)
    first_tag_id, second_tag_id = (tag.id for tag in library.tags[:2])

    panel.add_recent_tags([first_tag_id])
    panel.add_recent_tags([second_tag_id])
    panel.add_recent_tags([first_tag_id])

    assert panel.recent_tags.tag_ids == [first_tag_id, second_tag_id]


def test_recent_tags_leave_out_deleted_tags(
    qtbot: QtBot, library: Library, entry_state: EntryState, pinned_tags_state: PinnedTagsState
):
    panel = TaggingPanel(library, entry_state, pinned_tags_state)
    qtbot.addWidget(panel)
    first_tag_id, second_tag_id = (tag.id for tag in library.tags[-2:])
    panel.add_recent_tags([first_tag_id, second_tag_id])

    library.remove_tag(first_tag_id)

    assert panel.recent_tags.tag_ids == [second_tag_id]


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_pinned_tags_sorted_by_name(
    qtbot: QtBot, library: Library, entry_state: EntryState, pinned_tags_state: PinnedTagsState
):
    panel = TaggingPanel(library, entry_state, pinned_tags_state)
    qtbot.addWidget(panel)
    foo_id, bar_id = (library.get_tag_ids_by_name(name).pop() for name in ("foo", "bar"))

    pinned_tags_state.set_pinned(foo_id, is_pinned=True)
    pinned_tags_state.set_pinned(bar_id, is_pinned=True)

    assert panel.pinned_tags.tag_ids == [bar_id, foo_id]
