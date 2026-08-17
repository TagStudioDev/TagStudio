# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.mixed.folders_to_tags import folders_to_tags


def test_folders_to_tags(library: Library):
    folders_to_tags(library)
    entry = [x for x in library.all_entries(with_joins=True) if "bar.md" in str(x.path)][0]
    assert {x.name for x in entry.tags} == {"two", "bar"}
