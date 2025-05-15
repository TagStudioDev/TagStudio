import os
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtGui import (
    QAction,
)
from PySide6.QtWidgets import QMenu, QMenuBar
from pytestqt.qtbot import QtBot

from tagstudio.core.enums import ShowFilepathOption
from tagstudio.core.library.alchemy.library import Library, LibraryStatus
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.qt.modals.settings_panel import SettingsPanel
from tagstudio.qt.ts_qt import QtDriver
from tagstudio.qt.widgets.preview_panel import PreviewPanel


# Tests to see if the file path setting is applied correctly
@pytest.mark.parametrize(
    "filepath_option",
    [
        ShowFilepathOption.SHOW_FULL_PATHS.value,
        ShowFilepathOption.SHOW_RELATIVE_PATHS.value,
        ShowFilepathOption.SHOW_FILENAMES_ONLY.value,
    ],
)
def test_filepath_setting(qtbot: QtBot, qt_driver: QtDriver, filepath_option: ShowFilepathOption):
    settings_panel = SettingsPanel(qt_driver)
    qtbot.addWidget(settings_panel)

    # Mock the update_recent_lib_menu method
    with patch.object(qt_driver, "update_recent_lib_menu", return_value=None):
        # Set the file path option
        settings_panel.filepath_combobox.setCurrentIndex(filepath_option)
        settings_panel.update_settings(qt_driver)

        # Assert the setting is applied
        assert qt_driver.settings.show_filepath == filepath_option


# Tests to see if the file paths are being displayed correctly
@pytest.mark.parametrize(
    "filepath_option, expected_path",
    [
        (
            ShowFilepathOption.SHOW_FULL_PATHS,
            lambda library: Path(library.library_dir / "one/two/bar.md"),
        ),
        (ShowFilepathOption.SHOW_RELATIVE_PATHS, lambda _: Path("one/two/bar.md")),
        (ShowFilepathOption.SHOW_FILENAMES_ONLY, lambda _: Path("bar.md")),
    ],
)
def test_file_path_display(
    qt_driver: QtDriver, library: Library, filepath_option: ShowFilepathOption, expected_path
):
    panel = PreviewPanel(library, qt_driver)

    # Select 2
    qt_driver.toggle_item_selection(2, append=False, bridge=False)
    panel.update_widgets()

    qt_driver.settings.show_filepath = filepath_option

    # Apply the mock value
    entry = library.get_entry(2)
    assert isinstance(entry, Entry)
    filename = entry.path
    assert library.library_dir is not None
    panel.file_attrs.update_stats(filepath=library.library_dir / filename)

    # Generate the expected file string.
    # This is copied directly from the file_attributes.py file
    # can be imported as a function in the future
    display_path = expected_path(library)
    file_str: str = ""
    separator: str = f"<a style='color: #777777'><b>{os.path.sep}</a>"  # Gray
    for i, part in enumerate(display_path.parts):
        part_ = part.strip(os.path.sep)
        if i != len(display_path.parts) - 1:
            file_str += f"{'\u200b'.join(part_)}{separator}</b>"
        else:
            if file_str != "":
                file_str += "<br>"
            file_str += f"<b>{'\u200b'.join(part_)}</b>"

    # Assert the file path is displayed correctly
    assert panel.file_attrs.file_label.text() == file_str


@pytest.mark.parametrize(
    "filepath_option, expected_title",
    [
        (
            ShowFilepathOption.SHOW_FULL_PATHS.value,
            lambda path, base_title: f"{base_title} - Library '{path}'",
        ),
        (
            ShowFilepathOption.SHOW_RELATIVE_PATHS.value,
            lambda path, base_title: f"{base_title} - Library '{path.name}'",
        ),
        (
            ShowFilepathOption.SHOW_FILENAMES_ONLY.value,
            lambda path, base_title: f"{base_title} - Library '{path.name}'",
        ),
    ],
)
def test_title_update(
    qt_driver: QtDriver, filepath_option: ShowFilepathOption, expected_title, library_dir: Path
):
    base_title = qt_driver.base_title

    open_status = LibraryStatus(
        success=True,
        library_path=library_dir,
        message="",
        msg_description="",
    )
    # Set the file path option
    qt_driver.settings.show_filepath = filepath_option
    menu_bar = QMenuBar()

    qt_driver.open_recent_library_menu = QMenu(menu_bar)
    qt_driver.manage_file_ext_action = QAction(menu_bar)
    qt_driver.save_library_backup_action = QAction(menu_bar)
    qt_driver.close_library_action = QAction(menu_bar)
    qt_driver.refresh_dir_action = QAction(menu_bar)
    qt_driver.tag_manager_action = QAction(menu_bar)
    qt_driver.color_manager_action = QAction(menu_bar)
    qt_driver.new_tag_action = QAction(menu_bar)
    qt_driver.fix_dupe_files_action = QAction(menu_bar)
    qt_driver.fix_unlinked_entries_action = QAction(menu_bar)
    qt_driver.clear_thumb_cache_action = QAction(menu_bar)
    qt_driver.folders_to_tags_action = QAction(menu_bar)

    # Trigger the update
    qt_driver._init_library(library_dir, open_status)

    # Assert the title is updated correctly
    qt_driver.main_window.setWindowTitle.assert_called_with(expected_title(library_dir, base_title))
