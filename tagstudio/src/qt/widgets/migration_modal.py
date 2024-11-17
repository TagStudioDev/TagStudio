# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path

import structlog
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from src.core.constants import TS_FOLDER_NAME
from src.core.enums import LibraryPrefs
from src.core.library.alchemy.library import Library as SqliteLibrary
from src.core.library.json.library import Library as JsonLibrary  # type: ignore
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper
from src.qt.widgets.paged_panel.paged_body_wrapper import PagedBodyWrapper
from src.qt.widgets.paged_panel.paged_panel import PagedPanel
from src.qt.widgets.paged_panel.paged_panel_state import PagedPanelState

logger = structlog.get_logger(__name__)


class JsonMigrationModal(QObject):
    """A modal for data migration from v9.4 JSON to v9.5+ SQLite."""

    migration_cancelled = Signal()
    migration_finished = Signal()

    def __init__(self, path: Path):
        super().__init__()
        self.path: Path = path

        self.stack: list[PagedPanelState] = []
        self.json_lib: JsonLibrary = None
        self.sql_lib: SqliteLibrary = None
        self.is_migration_initialized: bool = False

        self.title: str = f'Save Format Migration: "{self.path}"'
        self.warning: str = "<b><a style='color: #e22c3c'>(!)</a></b>"

        self.old_entry_count: int = 0
        self.old_tag_count: int = 0
        self.old_ext_count: int = 0

        self.init_page_00()
        self.init_page_01()

        self.paged_panel: PagedPanel = PagedPanel((640, 320), self.stack)

    def init_page_00(self) -> None:
        body_wrapper: PagedBodyWrapper = PagedBodyWrapper()
        body_label: QLabel = QLabel(
            "Library save files created with TagStudio versions <b>9.4 and below</b> will "
            "need to be migrated to the new <b>v9.5+</b> format."
            "<br>"
            "<h2>What you need to know:</h2>"
            "<ul>"
            "<li>Your existing library save file will <b><i>NOT</i></b> be deleted</li>"
            "<li>Your personal files will <b><i>NOT</i></b> be deleted, moved, or modified</li>"
            "<li>The new v9.5+ save format can not be opened in earlier versions of TagStudio</li>"
            "</ul>"
        )
        body_label.setWordWrap(True)
        body_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        body_wrapper.layout().addWidget(body_label)

        cancel_button: QPushButtonWrapper = QPushButtonWrapper("Cancel")
        next_button: QPushButtonWrapper = QPushButtonWrapper("Continue")
        cancel_button.clicked.connect(self.migration_cancelled.emit)

        self.stack.append(
            PagedPanelState(
                title=self.title,
                body_wrapper=body_wrapper,
                buttons=[cancel_button, 1, next_button],
                connect_to_back=[cancel_button],
                connect_to_next=[next_button],
            )
        )

    def init_page_01(self) -> None:
        body_wrapper: PagedBodyWrapper = PagedBodyWrapper()
        body_container: QWidget = QWidget()
        body_container_layout: QHBoxLayout = QHBoxLayout(body_container)
        body_container_layout.setContentsMargins(0, 0, 0, 0)

        entries_text: str = "Entries:"
        tags_text: str = "Tags:"
        ext_text: str = "File Extension List:"
        desc_text: str = (
            "<br>Start and preview the results of the library migration process. "
            'The new converted library will not be used unless you click "Finish Migration". '
            "<i>This process may take up to several minutes for larger libraries.</i>"
        )

        old_lib_container: QWidget = QWidget()
        old_lib_layout: QVBoxLayout = QVBoxLayout(old_lib_container)
        old_lib_title: QLabel = QLabel("<h2>v9.4 Library</h2>")
        old_lib_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        old_lib_layout.addWidget(old_lib_title)

        old_content_container: QWidget = QWidget()
        self.old_content_layout: QGridLayout = QGridLayout(old_content_container)
        self.old_content_layout.setContentsMargins(0, 0, 0, 0)
        self.old_content_layout.addWidget(QLabel(entries_text), 0, 0)
        self.old_content_layout.addWidget(QLabel(tags_text), 1, 0)
        self.old_content_layout.addWidget(QLabel(ext_text), 2, 0)

        old_entry_count: QLabel = QLabel()
        old_entry_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_tag_count: QLabel = QLabel()
        old_tag_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_ext_count: QLabel = QLabel()
        old_ext_count.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.old_content_layout.addWidget(old_entry_count, 0, 1)
        self.old_content_layout.addWidget(old_tag_count, 1, 1)
        self.old_content_layout.addWidget(old_ext_count, 2, 1)
        old_lib_layout.addWidget(old_content_container)

        new_lib_container: QWidget = QWidget()
        new_lib_layout: QVBoxLayout = QVBoxLayout(new_lib_container)
        new_lib_title: QLabel = QLabel("<h2>v9.5+ Library</h2>")
        new_lib_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_lib_layout.addWidget(new_lib_title)

        new_content_container: QWidget = QWidget()
        self.new_content_layout: QGridLayout = QGridLayout(new_content_container)
        self.new_content_layout.setContentsMargins(0, 0, 0, 0)
        self.new_content_layout.addWidget(QLabel(entries_text), 0, 0)
        self.new_content_layout.addWidget(QLabel(tags_text), 1, 0)
        self.new_content_layout.addWidget(QLabel(ext_text), 2, 0)

        self.new_content_layout.addWidget(QLabel(), 0, 2)
        self.new_content_layout.addWidget(QLabel(), 1, 2)
        self.new_content_layout.addWidget(QLabel(), 2, 2)

        new_entry_count: QLabel = QLabel()
        new_entry_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        new_tag_count: QLabel = QLabel()
        new_tag_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        new_ext_count: QLabel = QLabel()
        new_ext_count.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.new_content_layout.addWidget(new_entry_count, 0, 1)
        self.new_content_layout.addWidget(new_tag_count, 1, 1)
        self.new_content_layout.addWidget(new_ext_count, 2, 1)
        new_lib_layout.addWidget(new_content_container)

        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)

        body_container_layout.addStretch(2)
        body_container_layout.addWidget(old_lib_container)
        body_container_layout.addStretch(1)
        body_container_layout.addWidget(new_lib_container)
        body_container_layout.addStretch(2)
        body_wrapper.layout().addWidget(body_container)
        body_wrapper.layout().addWidget(desc_label)

        back_button: QPushButtonWrapper = QPushButtonWrapper("Back")
        start_button: QPushButtonWrapper = QPushButtonWrapper("Start and Preview")
        start_button.setMinimumWidth(120)
        start_button.clicked.connect(self.init_migration)
        start_button.clicked.connect(lambda: finish_button.setDisabled(False))
        start_button.clicked.connect(lambda: start_button.setDisabled(True))
        finish_button: QPushButtonWrapper = QPushButtonWrapper("Finish Migration")
        finish_button.setMinimumWidth(120)
        finish_button.setDisabled(True)
        finish_button.clicked.connect(self.finish_migration)
        finish_button.clicked.connect(self.migration_finished.emit)

        self.stack.append(
            PagedPanelState(
                title=self.title,
                body_wrapper=body_wrapper,
                buttons=[back_button, 1, start_button, 1, finish_button],
                connect_to_back=[back_button],
                connect_to_next=[finish_button],
            )
        )

    def init_migration(self):
        if not self.is_migration_initialized:
            self.paged_panel.update_frame()
            self.paged_panel.update()

            # Initialize JSON Library
            self.json_lib = JsonLibrary()
            self.json_lib.open_library(self.path)

            self.update_old_entry_count(len(self.json_lib.entries))
            self.update_old_tag_count(len(self.json_lib.tags))
            self.update_old_ext_count(len(self.json_lib.ext_list))

            # Convert JSON Library to SQLite
            self.sql_lib = SqliteLibrary()
            self.temp_path: Path = (
                self.json_lib.library_dir / TS_FOLDER_NAME / "migration_ts_library.sqlite"
            )
            self.sql_lib.storage_path = self.temp_path
            if self.temp_path.exists():
                logger.info('Temporary migration file "temp_path" already exists. Removing...')
                self.temp_path.unlink()
            self.sql_lib.open_sqlite_library(self.temp_path, is_new=True, add_default_data=False)
            self.sql_lib.migrate_json_to_sqlite(self.json_lib)
            self.sql_lib.close()

            self.update_new_entry_count(self.sql_lib.entries_count)
            self.update_new_tag_count(len(self.sql_lib.tags))
            self.update_new_ext_count(len(self.sql_lib.prefs(LibraryPrefs.EXTENSION_LIST)))

            self.is_migration_initialized = True

    def finish_migration(self):
        final_name = self.json_lib.library_dir / TS_FOLDER_NAME / SqliteLibrary.SQL_FILENAME
        if self.temp_path.exists():
            self.temp_path.rename(final_name)

    def update_old_entry_count(self, value: int):
        self.old_entry_count = value
        label: QLabel = self.old_content_layout.itemAtPosition(0, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_old_tag_count(self, value: int):
        self.old_tag_count = value
        label: QLabel = self.old_content_layout.itemAtPosition(1, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_old_ext_count(self, value: int):
        self.old_ext_count = value
        label: QLabel = self.old_content_layout.itemAtPosition(2, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_new_entry_count(self, value: int):
        label: QLabel = self.new_content_layout.itemAtPosition(0, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(0, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_entry_count, value))
        warning_icon.setText("" if self.old_entry_count == value else self.warning)

    def update_new_tag_count(self, value: int):
        label: QLabel = self.new_content_layout.itemAtPosition(1, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(1, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_tag_count, value))
        warning_icon.setText("" if self.old_tag_count == value else self.warning)

    def update_new_ext_count(self, value: int):
        label: QLabel = self.new_content_layout.itemAtPosition(2, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(2, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_ext_count, value))
        warning_icon.setText("" if self.old_ext_count == value else self.warning)

    def color_value_default(self, value: int) -> str:
        """Apply the default color to a value."""
        return str(f"<b><a style='color: #3b87f0'>{value}</a></b>")

    def color_value_conditional(self, old_value: int, new_value: int) -> str:
        """Apply the default color to a value."""
        red: str = "#e22c3c"
        green: str = "#28bb48"
        color = green if old_value == new_value else red
        return str(f"<b><a style='color: {color}'>{new_value}</a></b>")
