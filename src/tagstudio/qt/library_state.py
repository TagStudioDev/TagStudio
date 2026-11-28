# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pydantic import Field

from tagstudio.core.utils.data_file import BaseDataFile

LIBRARY_STATE_NAME = "state.json"


class LibraryState(BaseDataFile):
    """Library state file for TagStudio."""

    pinned_tag_ids: list[int] = Field(default_factory=list)
