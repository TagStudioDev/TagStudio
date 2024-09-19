from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library
from src.core.library.alchemy.models import Folder
from src.qt.enums import WindowContent

if TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class LibraryDirsWidget(QWidget):
    library_dirs: list[Folder]

    def __init__(self, library: Library, driver: QtDriver):
        super().__init__()

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )

        self.driver = driver
        self.library = library

        # label and button
        self.create_panel()

        # actual library dirs
        self.items_layout = QVBoxLayout()
        self.root_layout.addLayout(self.items_layout)

        self.library_dirs = []
        # check if library is open
        self.refresh()

    def refresh(self):
        if not self.library.storage_path:
            return

        self.driver.main_window.set_main_content(WindowContent.LIBRARY_CONTENT)

        library_dirs = self.library.get_folders()
        if len(library_dirs) == len(self.library_dirs):
            # most likely no reason to refresh
            return

        self.library_dirs = library_dirs
        self.fill_dirs(self.library_dirs)

    def create_panel(self):
        label = QLabel("Library Folders")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        row_layout = QHBoxLayout()
        row_layout.addWidget(label)
        self.root_layout.addLayout(row_layout)

        # add a button which will open a library folder dialog
        button = QPushButton("Add Folder")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self.add_folder)
        self.root_layout.addWidget(button)

    def add_folder(self):
        """Open QT dialog to select a folder to add into library."""
        if not self.library.storage_path:
            # no library open, dont do anything
            return

        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory and (folder := self.library.add_folder(Path(directory))):
            self.driver.add_new_files_callback([folder])
            self.driver.filter_items()
            self.refresh()

    def fill_dirs(self, folders: list[Folder]) -> None:
        def clear_layout(layout_item: QVBoxLayout):
            for i in reversed(range(layout_item.count())):
                child = layout_item.itemAt(i)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    clear_layout(child.layout())  # type: ignore
                    # remove any potential previous items

        clear_layout(self.items_layout)

        for folder in folders:
            self.create_item(folder)

    def create_item(self, folder: Folder):
        def toggle_folder():
            self.driver.filter.toggle_folder(folder.id)
            self.driver.filter_items()

        button_toggle = QCheckBox()
        button_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        button_toggle.setFixedWidth(30)
        # TODO - figure out which one to check
        button_toggle.setChecked(True)  # item.id not in self.driver.filter.exclude_folders)

        button_toggle.clicked.connect(toggle_folder)

        folder_label = QLabel(folder.path.name)

        row_layout = QHBoxLayout()
        row_layout.addWidget(button_toggle)
        row_layout.addWidget(folder_label)

        self.items_layout.addLayout(row_layout)
