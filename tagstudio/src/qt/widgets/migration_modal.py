# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path

import structlog
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from src.core.constants import TS_FOLDER_NAME
from src.core.enums import LibraryPrefs
from src.core.library.alchemy.enums import FieldTypeEnum
from src.core.library.alchemy.fields import TagBoxField
from src.core.library.alchemy.joins import TagField, TagSubtag
from src.core.library.alchemy.library import Library as SqliteLibrary
from src.core.library.alchemy.models import Entry, Tag, TagAlias
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
        self.old_ext_type: bool = None

        self.init_page_info()
        self.init_page_convert()

        self.paged_panel: PagedPanel = PagedPanel((640, 460), self.stack)

    def init_page_info(self) -> None:
        """Initialize the migration info page."""
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

    def init_page_convert(self) -> None:
        """Initialize the migration conversion page."""
        body_wrapper: PagedBodyWrapper = PagedBodyWrapper()
        body_container: QWidget = QWidget()
        body_container_layout: QHBoxLayout = QHBoxLayout(body_container)
        body_container_layout.setContentsMargins(0, 0, 0, 0)

        tab: str = "     "
        self.match_text: str = "Matched"
        self.differ_text: str = "Discrepancy"

        entries_text: str = "Entries:"
        tags_text: str = "Tags:"
        shorthand_text: str = tab + "Shorthands:"
        subtags_text: str = tab + "Parent Tags:"
        aliases_text: str = tab + "Aliases:"
        ext_text: str = "File Extension List:"
        ext_type_text: str = "Extension List Type:"
        desc_text: str = (
            "<br>Start and preview the results of the library migration process. "
            'The converted library will <i>not</i> be used unless you click "Finish Migration". '
            "<br><br>"
            'Library data should either have matching values or a feature a "Matched" label. '
            'Values that do not match will be displayed in red and feature a "<b>(!)</b>" '
            "symbol next to them."
            "<br><center><i>"
            "This process may take up to several minutes for larger libraries."
            "</i></center>"
        )
        path_parity_text: str = tab + "Paths:"
        field_parity_text: str = tab + "Fields:"

        self.entries_row: int = 0
        self.path_row: int = 1
        self.fields_row: int = 2
        self.tags_row: int = 3
        self.shorthands_row: int = 4
        self.subtags_row: int = 5
        self.aliases_row: int = 6
        self.ext_row: int = 7
        self.ext_type_row: int = 8

        old_lib_container: QWidget = QWidget()
        old_lib_layout: QVBoxLayout = QVBoxLayout(old_lib_container)
        old_lib_title: QLabel = QLabel("<h2>v9.4 Library</h2>")
        old_lib_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        old_lib_layout.addWidget(old_lib_title)

        old_content_container: QWidget = QWidget()
        self.old_content_layout: QGridLayout = QGridLayout(old_content_container)
        self.old_content_layout.setContentsMargins(0, 0, 0, 0)
        self.old_content_layout.setSpacing(3)
        self.old_content_layout.addWidget(QLabel(entries_text), self.entries_row, 0)
        self.old_content_layout.addWidget(QLabel(path_parity_text), self.path_row, 0)
        self.old_content_layout.addWidget(QLabel(field_parity_text), self.fields_row, 0)
        self.old_content_layout.addWidget(QLabel(tags_text), self.tags_row, 0)
        self.old_content_layout.addWidget(QLabel(shorthand_text), self.shorthands_row, 0)
        self.old_content_layout.addWidget(QLabel(subtags_text), self.subtags_row, 0)
        self.old_content_layout.addWidget(QLabel(aliases_text), self.aliases_row, 0)
        self.old_content_layout.addWidget(QLabel(ext_text), self.ext_row, 0)
        self.old_content_layout.addWidget(QLabel(ext_type_text), self.ext_type_row, 0)

        old_entry_count: QLabel = QLabel()
        old_entry_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_path_value: QLabel = QLabel()
        old_path_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_field_value: QLabel = QLabel()
        old_field_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_tag_count: QLabel = QLabel()
        old_tag_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_shorthand_count: QLabel = QLabel()
        old_shorthand_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_subtag_value: QLabel = QLabel()
        old_subtag_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_alias_value: QLabel = QLabel()
        old_alias_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_ext_count: QLabel = QLabel()
        old_ext_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        old_ext_type: QLabel = QLabel()
        old_ext_type.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.old_content_layout.addWidget(old_entry_count, self.entries_row, 1)
        self.old_content_layout.addWidget(old_path_value, self.path_row, 1)
        self.old_content_layout.addWidget(old_field_value, self.fields_row, 1)
        self.old_content_layout.addWidget(old_tag_count, self.tags_row, 1)
        self.old_content_layout.addWidget(old_shorthand_count, self.shorthands_row, 1)
        self.old_content_layout.addWidget(old_subtag_value, self.subtags_row, 1)
        self.old_content_layout.addWidget(old_alias_value, self.aliases_row, 1)
        self.old_content_layout.addWidget(old_ext_count, self.ext_row, 1)
        self.old_content_layout.addWidget(old_ext_type, self.ext_type_row, 1)

        self.old_content_layout.addWidget(QLabel(), self.path_row, 2)
        self.old_content_layout.addWidget(QLabel(), self.fields_row, 2)
        self.old_content_layout.addWidget(QLabel(), self.shorthands_row, 2)
        self.old_content_layout.addWidget(QLabel(), self.subtags_row, 2)
        self.old_content_layout.addWidget(QLabel(), self.aliases_row, 2)

        old_lib_layout.addWidget(old_content_container)

        new_lib_container: QWidget = QWidget()
        new_lib_layout: QVBoxLayout = QVBoxLayout(new_lib_container)
        new_lib_title: QLabel = QLabel("<h2>v9.5+ Library</h2>")
        new_lib_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_lib_layout.addWidget(new_lib_title)

        new_content_container: QWidget = QWidget()
        self.new_content_layout: QGridLayout = QGridLayout(new_content_container)
        self.new_content_layout.setContentsMargins(0, 0, 0, 0)
        self.new_content_layout.setSpacing(3)
        self.new_content_layout.addWidget(QLabel(entries_text), self.entries_row, 0)
        self.new_content_layout.addWidget(QLabel(path_parity_text), self.path_row, 0)
        self.new_content_layout.addWidget(QLabel(field_parity_text), self.fields_row, 0)
        self.new_content_layout.addWidget(QLabel(tags_text), self.tags_row, 0)
        self.new_content_layout.addWidget(QLabel(shorthand_text), self.shorthands_row, 0)
        self.new_content_layout.addWidget(QLabel(subtags_text), self.subtags_row, 0)
        self.new_content_layout.addWidget(QLabel(aliases_text), self.aliases_row, 0)
        self.new_content_layout.addWidget(QLabel(ext_text), self.ext_row, 0)
        self.new_content_layout.addWidget(QLabel(ext_type_text), self.ext_type_row, 0)

        new_entry_count: QLabel = QLabel()
        new_entry_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        path_parity_value: QLabel = QLabel()
        path_parity_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        field_parity_value: QLabel = QLabel()
        field_parity_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        new_tag_count: QLabel = QLabel()
        new_tag_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        new_shorthand_count: QLabel = QLabel()
        new_shorthand_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        subtag_parity_value: QLabel = QLabel()
        subtag_parity_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        alias_parity_value: QLabel = QLabel()
        alias_parity_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        new_ext_count: QLabel = QLabel()
        new_ext_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        new_ext_type: QLabel = QLabel()
        new_ext_type.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.new_content_layout.addWidget(new_entry_count, self.entries_row, 1)
        self.new_content_layout.addWidget(path_parity_value, self.path_row, 1)
        self.new_content_layout.addWidget(field_parity_value, self.fields_row, 1)
        self.new_content_layout.addWidget(new_tag_count, self.tags_row, 1)
        self.new_content_layout.addWidget(new_shorthand_count, self.shorthands_row, 1)
        self.new_content_layout.addWidget(subtag_parity_value, self.subtags_row, 1)
        self.new_content_layout.addWidget(alias_parity_value, self.aliases_row, 1)
        self.new_content_layout.addWidget(new_ext_count, self.ext_row, 1)
        self.new_content_layout.addWidget(new_ext_type, self.ext_type_row, 1)

        self.new_content_layout.addWidget(QLabel(), self.entries_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.path_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.fields_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.shorthands_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.tags_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.subtags_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.aliases_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.ext_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.ext_type_row, 2)

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
        start_button.clicked.connect(self.migrate)
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

    def migrate(self):
        """Open and migrate the JSON library to SQLite."""
        if not self.is_migration_initialized:
            self.paged_panel.update_frame()
            self.paged_panel.update()

            # Open the JSON Library
            self.json_lib = JsonLibrary()
            self.json_lib.open_library(self.path)

            # Update JSON UI
            self.update_json_entry_count(len(self.json_lib.entries))
            self.update_json_tag_count(len(self.json_lib.tags))
            self.update_json_ext_count(len(self.json_lib.ext_list))
            self.update_json_ext_type(self.json_lib.is_exclude_list)

            # Convert JSON Library to SQLite
            self.sql_lib = SqliteLibrary()
            self.temp_path: Path = (
                self.json_lib.library_dir / TS_FOLDER_NAME / "migration_ts_library.sqlite"
            )
            self.sql_lib.storage_path = self.temp_path
            if self.temp_path.exists():
                logger.info('Temporary migration file "temp_path" already exists. Removing...')
                self.temp_path.unlink()
            self.sql_lib.open_sqlite_library(
                self.json_lib.library_dir, is_new=True, add_default_data=False
            )
            self.sql_lib.migrate_json_to_sqlite(self.json_lib)
            self.update_field_parity_value(self.check_field_parity())
            self.update_path_parity_value(self.check_path_parity())
            self.update_shorthand_parity_value(self.check_shorthand_parity())
            self.update_subtag_parity_value(self.check_subtag_parity())
            self.update_alias_parity_value(self.check_alias_parity())
            self.sql_lib.close()

            # Update SQLite UI
            self.update_sql_entry_count(self.sql_lib.entries_count)
            self.update_sql_tag_count(len(self.sql_lib.tags))
            self.update_sql_ext_count(len(self.sql_lib.prefs(LibraryPrefs.EXTENSION_LIST)))
            self.update_sql_ext_type(self.sql_lib.prefs(LibraryPrefs.IS_EXCLUDE_LIST))
            QApplication.beep()

            self.is_migration_initialized = True

    def finish_migration(self):
        """Finish the migration upon user approval."""
        final_name = self.json_lib.library_dir / TS_FOLDER_NAME / SqliteLibrary.SQL_FILENAME
        if self.temp_path.exists():
            self.temp_path.rename(final_name)

    def update_json_entry_count(self, value: int):
        self.old_entry_count = value
        label: QLabel = self.old_content_layout.itemAtPosition(self.entries_row, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_json_tag_count(self, value: int):
        self.old_tag_count = value
        label: QLabel = self.old_content_layout.itemAtPosition(self.tags_row, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_json_ext_count(self, value: int):
        self.old_ext_count = value
        label: QLabel = self.old_content_layout.itemAtPosition(self.ext_row, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_json_ext_type(self, value: bool):
        self.old_ext_type = value
        label: QLabel = self.old_content_layout.itemAtPosition(self.ext_type_row, 1).widget()  # type:ignore
        label.setText(self.color_value_default(value))

    def update_sql_entry_count(self, value: int):
        label: QLabel = self.new_content_layout.itemAtPosition(self.entries_row, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(self.entries_row, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_entry_count, value))
        warning_icon.setText("" if self.old_entry_count == value else self.warning)

    def update_path_parity_value(self, value: bool):
        result: str = self.match_text if value else self.differ_text
        old_label: QLabel = self.old_content_layout.itemAtPosition(self.path_row, 1).widget()  # type:ignore
        new_label: QLabel = self.new_content_layout.itemAtPosition(self.path_row, 1).widget()  # type:ignore
        old_warning_icon: QLabel = self.old_content_layout.itemAtPosition(self.path_row, 2).widget()  # type:ignore
        new_warning_icon: QLabel = self.new_content_layout.itemAtPosition(self.path_row, 2).widget()  # type:ignore
        old_label.setText(self.color_value_conditional(self.match_text, result))
        new_label.setText(self.color_value_conditional(self.match_text, result))
        old_warning_icon.setText("" if value else self.warning)
        new_warning_icon.setText("" if value else self.warning)

    def update_field_parity_value(self, value: bool):
        result: str = self.match_text if value else self.differ_text
        old_label: QLabel = self.old_content_layout.itemAtPosition(self.fields_row, 1).widget()  # type:ignore
        new_label: QLabel = self.new_content_layout.itemAtPosition(self.fields_row, 1).widget()  # type:ignore
        old_warning_icon: QLabel = self.old_content_layout.itemAtPosition(
            self.fields_row, 2
        ).widget()  # type:ignore
        new_warning_icon: QLabel = self.new_content_layout.itemAtPosition(
            self.fields_row, 2
        ).widget()  # type:ignore
        old_label.setText(self.color_value_conditional(self.match_text, result))
        new_label.setText(self.color_value_conditional(self.match_text, result))
        old_warning_icon.setText("" if value else self.warning)
        new_warning_icon.setText("" if value else self.warning)

    def update_sql_tag_count(self, value: int):
        label: QLabel = self.new_content_layout.itemAtPosition(self.tags_row, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(self.tags_row, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_tag_count, value))
        warning_icon.setText("" if self.old_tag_count == value else self.warning)

    def update_shorthand_parity_value(self, value: bool):
        result: str = self.match_text if value else self.differ_text
        old_label: QLabel = self.old_content_layout.itemAtPosition(self.shorthands_row, 1).widget()  # type:ignore
        new_label: QLabel = self.new_content_layout.itemAtPosition(self.shorthands_row, 1).widget()  # type:ignore
        old_warning_icon: QLabel = self.old_content_layout.itemAtPosition(
            self.shorthands_row, 2
        ).widget()  # type:ignore
        new_warning_icon: QLabel = self.new_content_layout.itemAtPosition(
            self.shorthands_row, 2
        ).widget()  # type:ignore
        old_label.setText(self.color_value_conditional(self.match_text, result))
        new_label.setText(self.color_value_conditional(self.match_text, result))
        old_warning_icon.setText("" if value else self.warning)
        new_warning_icon.setText("" if value else self.warning)

    def update_subtag_parity_value(self, value: bool):
        result: str = self.match_text if value else self.differ_text
        old_label: QLabel = self.old_content_layout.itemAtPosition(self.subtags_row, 1).widget()  # type:ignore
        new_label: QLabel = self.new_content_layout.itemAtPosition(self.subtags_row, 1).widget()  # type:ignore
        old_warning_icon: QLabel = self.old_content_layout.itemAtPosition(
            self.subtags_row, 2
        ).widget()  # type:ignore
        new_warning_icon: QLabel = self.new_content_layout.itemAtPosition(
            self.subtags_row, 2
        ).widget()  # type:ignore
        old_label.setText(self.color_value_conditional(self.match_text, result))
        new_label.setText(self.color_value_conditional(self.match_text, result))
        old_warning_icon.setText("" if value else self.warning)
        new_warning_icon.setText("" if value else self.warning)

    def update_alias_parity_value(self, value: bool):
        result: str = self.match_text if value else self.differ_text
        old_label: QLabel = self.old_content_layout.itemAtPosition(self.aliases_row, 1).widget()  # type:ignore
        new_label: QLabel = self.new_content_layout.itemAtPosition(self.aliases_row, 1).widget()  # type:ignore
        old_warning_icon: QLabel = self.old_content_layout.itemAtPosition(
            self.aliases_row, 2
        ).widget()  # type:ignore
        new_warning_icon: QLabel = self.new_content_layout.itemAtPosition(
            self.aliases_row, 2
        ).widget()  # type:ignore
        old_label.setText(self.color_value_conditional(self.match_text, result))
        new_label.setText(self.color_value_conditional(self.match_text, result))
        old_warning_icon.setText("" if value else self.warning)
        new_warning_icon.setText("" if value else self.warning)

    def update_sql_ext_count(self, value: int):
        label: QLabel = self.new_content_layout.itemAtPosition(self.ext_row, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(self.ext_row, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_ext_count, value))
        warning_icon.setText("" if self.old_ext_count == value else self.warning)

    def update_sql_ext_type(self, value: bool):
        label: QLabel = self.new_content_layout.itemAtPosition(self.ext_type_row, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(self.ext_type_row, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(self.old_ext_type, value))
        warning_icon.setText("" if self.old_ext_type == value else self.warning)

    def color_value_default(self, value: int) -> str:
        """Apply the default color to a value."""
        return str(f"<b><a style='color: #3b87f0'>{value}</a></b>")

    def color_value_conditional(self, old_value: int | str, new_value: int | str) -> str:
        """Apply a conditional color to a value."""
        red: str = "#e22c3c"
        green: str = "#28bb48"
        color = green if old_value == new_value else red
        return str(f"<b><a style='color: {color}'>{new_value}</a></b>")

    def check_field_parity(self, logging: bool = False) -> bool:
        """Check if all JSON field data matches the new SQL field data."""

        def sanitize_field(session, entry: Entry, value, type, type_key):
            if type is FieldTypeEnum.TAGS:
                tags = list(
                    session.scalars(
                        select(Tag.id)
                        .join(TagField)
                        .join(TagBoxField)
                        .where(
                            and_(
                                TagBoxField.entry_id == entry.id,
                                TagBoxField.id == TagField.field_id,
                                TagBoxField.type_key == type_key,
                            )
                        )
                    )
                )

                return set(tags) if tags else None
            else:
                return value if value else None

        def sanitize_json_field(value):
            if isinstance(value, list):
                return set(value) if value else None
            else:
                return value if value else None

        with Session(self.sql_lib.engine) as session:
            for json_entry in self.json_lib.entries:
                sql_entry: Entry = session.scalar(
                    select(Entry).where(Entry.id == json_entry.id + 1)
                )
                if not sql_entry:
                    continue

                sql_fields: list[tuple] = []

                for field in sql_entry.fields:
                    sql_fields.append(
                        (
                            field.type.key,
                            sanitize_field(
                                session, sql_entry, field.value, field.type.type, field.type_key
                            ),
                        )
                    )
                sql_fields.sort()
                json_fields = [
                    (
                        self.sql_lib.get_field_name_from_id(list(x.keys())[0]).name,
                        sanitize_json_field(list(x.values())[0]),
                    )
                    for x in json_entry.fields
                ]
                json_fields.sort()
                if logging:
                    logger.info(json_fields)
                    logger.info("--------------------------------------")
                    logger.info(sql_fields)
                    logger.info("\n")

        return json_fields == sql_fields

    def check_path_parity(self) -> bool:
        """Check if all JSON file paths match the new SQL paths."""
        with Session(self.sql_lib.engine) as session:
            json_paths: list = sorted([x.path / x.filename for x in self.json_lib.entries])
            sql_paths: list = sorted(list(session.scalars(select(Entry.path))))
        return json_paths == sql_paths

    def check_subtag_parity(self, logging: bool = False) -> bool:
        """Check if all JSON subtags match the new SQL subtags."""
        with Session(self.sql_lib.engine) as session:
            sql_subtags: list[set[int]] = []
            json_subtags: list[set[int]] = []

            for sql_tag in self.sql_lib.tags:
                subtags = set(
                    session.scalars(
                        select(TagSubtag.child_id).where(TagSubtag.parent_id == sql_tag.id)
                    )
                )
                sql_subtags.append(subtags)
            sql_subtags.sort()

            for json_tag in self.json_lib.tags:
                json_subtags.append(set(json_tag.subtag_ids).difference(set([json_tag.id])))
            json_subtags.sort()

            if logging:
                logger.info(json_subtags)
                logger.info("--------------------------------------")
                logger.info(sql_subtags)
                logger.info("\n")

        return sql_subtags == json_subtags

    def check_ext_type(self) -> bool:
        return self.json_lib.is_exclude_list == self.sql_lib.prefs(LibraryPrefs.IS_EXCLUDE_LIST)

    def check_alias_parity(self, logging: bool = False) -> bool:
        """Check if all JSON aliases match the new SQL aliases."""
        with Session(self.sql_lib.engine) as session:
            sql_aliases: list[set[str]] = []
            json_aliases: list[set[str]] = []

            for sql_tag in self.sql_lib.tags:
                aliases = set(
                    session.scalars(select(TagAlias.name).where(TagAlias.tag_id == sql_tag.id))
                )
                sql_aliases.append(aliases)
            sql_aliases.sort()

            for json_tag in self.json_lib.tags:
                json_aliases.append(set(json_tag.aliases))
            json_aliases.sort()

            if logging:
                logger.info(json_aliases)
                logger.info("--------------------------------------")
                logger.info(sql_aliases)
                logger.info("\n")

        return sql_aliases == json_aliases

    def check_shorthand_parity(self, logging: bool = False) -> bool:
        """Check if all JSON shorthands match the new SQL shorthands."""
        with Session(self.sql_lib.engine) as session:
            sql_shorthands: list[set[str]] = []
            json_shorthands: list[set[str]] = []

            for sql_tag in self.sql_lib.tags:
                shorthands = set(
                    session.scalars(select(TagAlias.name).where(TagAlias.tag_id == sql_tag.id))
                )
                sql_shorthands.append(shorthands)
            sql_shorthands.sort()

            for json_tag in self.json_lib.tags:
                json_shorthands.append(set(json_tag.aliases))
            json_shorthands.sort()

            if logging:
                logger.info(json_shorthands)
                logger.info("--------------------------------------")
                logger.info(sql_shorthands)
                logger.info("\n")

        return sql_shorthands == json_shorthands
