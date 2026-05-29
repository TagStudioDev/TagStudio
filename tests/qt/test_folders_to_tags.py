# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.mixed.folders_to_tags import BranchData, generate_preview_data


def test_generate_preview_data(library: Library, snapshot: BranchData):
    preview = generate_preview_data(library)

    assert preview == snapshot
