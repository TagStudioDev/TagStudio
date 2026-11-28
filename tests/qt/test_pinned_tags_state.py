# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from tempfile import TemporaryDirectory

import pytest

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.pinned_tags_state import PinnedTagsState


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_pinned_tags_load_from_library_state_file(library: Library):
    state = PinnedTagsState(library)
    state.load()
    state.set_pinned(TAG_ARCHIVED, is_pinned=True)
    state.set_pinned(TAG_FAVORITE, is_pinned=True)

    reloaded_state = PinnedTagsState(library)
    reloaded_state.load()

    assert reloaded_state.tag_ids == {TAG_ARCHIVED, TAG_FAVORITE}


@pytest.mark.parametrize("library", [TemporaryDirectory()], indirect=True)
def test_pinned_tags_leave_out_deleted_tags(library: Library, pinned_tags_state: PinnedTagsState):
    tag_id = library.tags[-1].id
    pinned_tags_state.set_pinned(tag_id, is_pinned=True)
    library.remove_tag(tag_id)

    pinned_tags_state.load()

    assert pinned_tags_state.tag_ids == set()
