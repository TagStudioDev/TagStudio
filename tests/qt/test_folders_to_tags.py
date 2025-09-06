# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.mixed.folders_to_tags import BranchData, generate_preview_data


def test_generate_preview_data(library: Library, snapshot: BranchData):
    preview = generate_preview_data(library)

    assert preview == snapshot
