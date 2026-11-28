# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from tempfile import TemporaryDirectory

import pytest

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.tag_lists_state import TagListsState


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_pinned_tags_load_from_library_state_file(library: Library):
    state = TagListsState(library)
    state.load()
    state.set_pinned(TAG_ARCHIVED, is_pinned=True)
    state.set_pinned(TAG_FAVORITE, is_pinned=True)

    reloaded_state = TagListsState(library)
    reloaded_state.load()

    assert reloaded_state.pinned_tag_ids == {TAG_ARCHIVED, TAG_FAVORITE}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_pinned_tags_leave_out_deleted_tags(library: Library, tag_lists_state: TagListsState):
    tag_id = library.tags[-1].id
    tag_lists_state.set_pinned(tag_id, is_pinned=True)
    library.remove_tag(tag_id)

    tag_lists_state.load()

    assert tag_lists_state.pinned_tag_ids == set()


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_recent_tags_load_from_library_state_file(tag_lists_state: TagListsState):
    tag_lists_state.add_recent_tags([TAG_ARCHIVED, TAG_FAVORITE])
    tag_lists_state.close()

    tag_lists_state.load()

    assert tag_lists_state.recent_tag_ids == [TAG_ARCHIVED, TAG_FAVORITE]
