# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.modals.tag_search import TagSearchPanel


def test_update_tags(qtbot: QtBot, library: Library):
    # Given
    panel = TagSearchPanel(library)

    qtbot.addWidget(panel)

    # When
    panel.update_tags()
