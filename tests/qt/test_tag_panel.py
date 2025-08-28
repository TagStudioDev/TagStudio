# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from pytestqt.qtbot import QtBot

from tagstudio.core.library.alchemy.library import Library, Tag
from tagstudio.qt.modals.build_tag import BuildTagPanel
from tagstudio.qt.ts_qt import QtDriver


def test_tag_panel(qtbot: QtBot, library: Library):
    panel = BuildTagPanel(library)

    qtbot.addWidget(panel)


def test_add_tag_callback(qt_driver: QtDriver):
    # Given
    assert len(qt_driver.lib.tags) == 6
    qt_driver.add_tag_action_callback()

    # When
    assert isinstance(qt_driver.modal.widget, BuildTagPanel)
    qt_driver.modal.widget.name_field.setText("xxx")
    # qt_driver.modal.widget.color_field.setCurrentIndex(1)
    qt_driver.modal.saved.emit()

    # Then
    tags: list[Tag] = qt_driver.lib.tags
    assert len(tags) == 7
    assert "xxx" in {tag.name for tag in tags}
