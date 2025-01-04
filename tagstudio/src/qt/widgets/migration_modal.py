# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path

import structlog
from PySide6.QtCore import QObject, Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.core.constants import TS_FOLDER_NAME
from src.core.enums import LibraryPrefs
from src.core.library.alchemy.enums import TagColor
from src.core.library.alchemy.joins import TagSubtag
from src.core.library.alchemy.library import DEFAULT_TAG_DIFF
from src.core.library.alchemy.library import Library as SqliteLibrary
from src.core.library.alchemy.models import Entry, TagAlias
from src.core.library.json.library import Library as JsonLibrary  # type: ignore
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.helpers.function_iterator import FunctionIterator
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper
from src.qt.translations import Translations
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
        self.done: bool = False
        self.path: Path = path

        self.stack: list[PagedPanelState] = []
        self.json_lib: JsonLibrary = None
        self.sql_lib: SqliteLibrary = None
        self.is_migration_initialized: bool = False
        self.discrepancies: list[str] = []

        self.title: str = Translations.translate_formatted("json_migration.title", path=self.path)
        self.warning: str = "<b><a style='color: #e22c3c'>(!)</a></b>"

        self.old_entry_count: int = 0
        self.old_tag_count: int = 0
        self.old_ext_count: int = 0
        self.old_ext_type: bool = None

        self.field_parity: bool = False
        self.path_parity: bool = False
        self.shorthand_parity: bool = False
        self.subtag_parity: bool = False
        self.alias_parity: bool = False
        self.color_parity: bool = False

        self.init_page_info()
        self.init_page_convert()

        self.paged_panel: PagedPanel = PagedPanel((700, 640), self.stack)

    def init_page_info(self) -> None:
        """Initialize the migration info page."""
        body_wrapper: PagedBodyWrapper = PagedBodyWrapper()
        body_label = QLabel()
        Translations.translate_qobject(body_label, "json_migration.info.description")
        body_label.setWordWrap(True)
        body_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        body_wrapper.layout().addWidget(body_label)
        body_wrapper.layout().setContentsMargins(0, 36, 0, 0)

        cancel_button = QPushButtonWrapper()
        Translations.translate_qobject(cancel_button, "generic.cancel")
        next_button = QPushButtonWrapper()
        Translations.translate_qobject(next_button, "generic.continue")
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
        self.body_wrapper_01: PagedBodyWrapper = PagedBodyWrapper()
        body_container: QWidget = QWidget()
        body_container_layout: QHBoxLayout = QHBoxLayout(body_container)
        body_container_layout.setContentsMargins(0, 0, 0, 0)

        tab: str = "     "
        self.match_text: str = Translations["json_migration.heading.match"]
        self.differ_text: str = Translations["json_migration.heading.differ"]

        entries_text: str = Translations["json_migration.heading.entires"]
        tags_text: str = Translations["json_migration.heading.tags"]
        shorthand_text: str = tab + Translations["json_migration.heading.shorthands"]
        subtags_text: str = tab + Translations["json_migration.heading.parent_tags"]
        aliases_text: str = tab + Translations["json_migration.heading.aliases"]
        colors_text: str = tab + Translations["json_migration.heading.colors"]
        ext_text: str = Translations["json_migration.heading.file_extension_list"]
        ext_type_text: str = Translations["json_migration.heading.extension_list_type"]
        desc_text: str = Translations["json_migration.description"]
        path_parity_text: str = tab + Translations["json_migration.heading.paths"]
        field_parity_text: str = tab + Translations["json_migration.heading.fields"]

        self.entries_row: int = 0
        self.path_row: int = 1
        self.fields_row: int = 2
        self.tags_row: int = 3
        self.shorthands_row: int = 4
        self.subtags_row: int = 5
        self.aliases_row: int = 6
        self.colors_row: int = 7
        self.ext_row: int = 8
        self.ext_type_row: int = 9

        old_lib_container: QWidget = QWidget()
        old_lib_layout: QVBoxLayout = QVBoxLayout(old_lib_container)
        old_lib_title = QLabel()
        Translations.translate_qobject(old_lib_title, "json_migration.title.old_lib")
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
        self.old_content_layout.addWidget(QLabel(colors_text), self.colors_row, 0)
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
        old_color_value: QLabel = QLabel()
        old_color_value.setAlignment(Qt.AlignmentFlag.AlignRight)
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
        self.old_content_layout.addWidget(old_color_value, self.colors_row, 1)
        self.old_content_layout.addWidget(old_ext_count, self.ext_row, 1)
        self.old_content_layout.addWidget(old_ext_type, self.ext_type_row, 1)

        self.old_content_layout.addWidget(QLabel(), self.path_row, 2)
        self.old_content_layout.addWidget(QLabel(), self.fields_row, 2)
        self.old_content_layout.addWidget(QLabel(), self.shorthands_row, 2)
        self.old_content_layout.addWidget(QLabel(), self.subtags_row, 2)
        self.old_content_layout.addWidget(QLabel(), self.aliases_row, 2)
        self.old_content_layout.addWidget(QLabel(), self.colors_row, 2)

        old_lib_layout.addWidget(old_content_container)

        new_lib_container: QWidget = QWidget()
        new_lib_layout: QVBoxLayout = QVBoxLayout(new_lib_container)
        new_lib_title = QLabel()
        Translations.translate_qobject(new_lib_title, "json_migration.title.new_lib")
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
        self.new_content_layout.addWidget(QLabel(colors_text), self.colors_row, 0)
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
        new_color_value: QLabel = QLabel()
        new_color_value.setAlignment(Qt.AlignmentFlag.AlignRight)
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
        self.new_content_layout.addWidget(new_color_value, self.colors_row, 1)
        self.new_content_layout.addWidget(new_ext_count, self.ext_row, 1)
        self.new_content_layout.addWidget(new_ext_type, self.ext_type_row, 1)

        self.new_content_layout.addWidget(QLabel(), self.entries_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.path_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.fields_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.shorthands_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.tags_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.subtags_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.aliases_row, 2)
        self.new_content_layout.addWidget(QLabel(), self.colors_row, 2)
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
        self.body_wrapper_01.layout().addWidget(body_container)
        self.body_wrapper_01.layout().addWidget(desc_label)
        self.body_wrapper_01.layout().setSpacing(12)

        back_button = QPushButtonWrapper()
        Translations.translate_qobject(back_button, "generic.navigation.back")
        start_button = QPushButtonWrapper()
        Translations.translate_qobject(start_button, "json_migration.start_and_preview")
        start_button.setMinimumWidth(120)
        start_button.clicked.connect(self.migrate)
        start_button.clicked.connect(lambda: finish_button.setDisabled(False))
        start_button.clicked.connect(lambda: start_button.setDisabled(True))
        finish_button: QPushButtonWrapper = QPushButtonWrapper()
        Translations.translate_qobject(finish_button, "json_migration.finish_migration")
        finish_button.setMinimumWidth(120)
        finish_button.setDisabled(True)
        finish_button.clicked.connect(self.finish_migration)
        finish_button.clicked.connect(self.migration_finished.emit)

        self.stack.append(
            PagedPanelState(
                title=self.title,
                body_wrapper=self.body_wrapper_01,
                buttons=[back_button, 1, start_button, 1, finish_button],
                connect_to_back=[back_button],
                connect_to_next=[finish_button],
            )
        )

    def migrate(self, skip_ui: bool = False):
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

            self.migration_progress(skip_ui=skip_ui)
            self.is_migration_initialized = True

    def migration_progress(self, skip_ui: bool = False):
        """Initialize the progress bar and iterator for the library migration."""
        pb = QProgressDialog(
            labelText="",
            cancelButtonText="",
            minimum=0,
            maximum=0,
        )
        pb.setCancelButton(None)
        self.body_wrapper_01.layout().addWidget(pb)

        iterator = FunctionIterator(self.migration_iterator)
        iterator.value.connect(
            lambda x: (
                pb.setLabelText(f"<h4>{x}</h4>"),
                self.update_sql_value_ui(show_msg_box=False)
                if x == Translations["json_migration.checking_for_parity"]
                else (),
                self.update_parity_ui()
                if x == Translations["json_migration.checking_for_parity"]
                else (),
            )
        )
        r = CustomRunnable(iterator.run)
        r.done.connect(
            lambda: (
                self.update_sql_value_ui(show_msg_box=not skip_ui),
                pb.setMinimum(1),
                pb.setValue(1),
            )
        )
        QThreadPool.globalInstance().start(r)

    def migration_iterator(self):
        """Iterate over the library migration process."""
        try:
            # Convert JSON Library to SQLite
            yield Translations["json_migration.creating_database_tables"]
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
            yield Translations.translate_formatted(
                "json_migration.migrating_files_entries", entries=len(self.json_lib.entries)
            )
            self.sql_lib.migrate_json_to_sqlite(self.json_lib)
            yield Translations["json_migration.checking_for_parity"]
            check_set = set()
            check_set.add(self.check_field_parity())
            check_set.add(self.check_path_parity())
            check_set.add(self.check_shorthand_parity())
            check_set.add(self.check_subtag_parity())
            check_set.add(self.check_alias_parity())
            check_set.add(self.check_color_parity())
            self.update_parity_ui()
            if False not in check_set:
                yield Translations["json_migration.migration_complete"]
            else:
                yield Translations["json_migration.migration_complete_with_discrepancies"]
            self.done = True

        except Exception as e:
            yield f"Error: {type(e).__name__}"
        self.done = True

    def update_parity_ui(self):
        """Update all parity values UI."""
        self.update_parity_value(self.fields_row, self.field_parity)
        self.update_parity_value(self.path_row, self.path_parity)
        self.update_parity_value(self.shorthands_row, self.shorthand_parity)
        self.update_parity_value(self.subtags_row, self.subtag_parity)
        self.update_parity_value(self.aliases_row, self.alias_parity)
        self.update_parity_value(self.colors_row, self.color_parity)
        self.sql_lib.close()

    def update_sql_value_ui(self, show_msg_box: bool = True):
        """Update the SQL value count UI."""
        self.update_sql_value(
            self.entries_row,
            self.sql_lib.entries_count,
            self.old_entry_count,
        )
        self.update_sql_value(
            self.tags_row,
            (len(self.sql_lib.tags) - DEFAULT_TAG_DIFF),
            self.old_tag_count,
        )
        self.update_sql_value(
            self.ext_row,
            len(self.sql_lib.prefs(LibraryPrefs.EXTENSION_LIST)),
            self.old_ext_count,
        )
        self.update_sql_value(
            self.ext_type_row,
            self.sql_lib.prefs(LibraryPrefs.IS_EXCLUDE_LIST),
            self.old_ext_type,
        )
        logger.info("Parity check complete!")
        if self.discrepancies:
            logger.warning("Discrepancies found:")
            logger.warning("\n".join(self.discrepancies))
            QApplication.beep()
            if not show_msg_box:
                return
            msg_box = QMessageBox()
            Translations.translate_with_setter(
                msg_box.setWindowTitle, "json_migration.discrepancies_found"
            )
            Translations.translate_qobject(
                msg_box, "json_migration.discrepancies_found.description"
            )
            msg_box.setDetailedText("\n".join(self.discrepancies))
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.exec()

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

    def update_sql_value(self, row: int, value: int | bool, old_value: int | bool):
        label: QLabel = self.new_content_layout.itemAtPosition(row, 1).widget()  # type:ignore
        warning_icon: QLabel = self.new_content_layout.itemAtPosition(row, 2).widget()  # type:ignore
        label.setText(self.color_value_conditional(old_value, value))
        warning_icon.setText("" if old_value == value else self.warning)

    def update_parity_value(self, row: int, value: bool):
        result: str = self.match_text if value else self.differ_text
        old_label: QLabel = self.old_content_layout.itemAtPosition(row, 1).widget()  # type:ignore
        new_label: QLabel = self.new_content_layout.itemAtPosition(row, 1).widget()  # type:ignore
        old_warning_icon: QLabel = self.old_content_layout.itemAtPosition(row, 2).widget()  # type:ignore
        new_warning_icon: QLabel = self.new_content_layout.itemAtPosition(row, 2).widget()  # type:ignore
        old_label.setText(self.color_value_conditional(self.match_text, result))
        new_label.setText(self.color_value_conditional(self.match_text, result))
        old_warning_icon.setText("" if value else self.warning)
        new_warning_icon.setText("" if value else self.warning)

    def color_value_default(self, value: int) -> str:
        """Apply the default color to a value."""
        return str(f"<b><a style='color: #3b87f0'>{value}</a></b>")

    def color_value_conditional(self, old_value: int | str, new_value: int | str) -> str:
        """Apply a conditional color to a value."""
        red: str = "#e22c3c"
        green: str = "#28bb48"
        color = green if old_value == new_value else red
        return str(f"<b><a style='color: {color}'>{new_value}</a></b>")

    def check_field_parity(self) -> bool:
        """Check if all JSON field data matches the new SQL field data."""

        def sanitize_field(session, entry: Entry, value, type, type_key):
            #            if type is FieldTypeEnum.TAGS:
            #                tags = list(
            #                    session.scalars(
            #                        select(Tag.id)
            #                        .join(TagField)
            #                        .join(TagBoxField)
            #                        .where(
            #                            and_(
            #                                TagBoxField.entry_id == entry.id,
            #                                TagBoxField.id == TagField.field_id,
            #                                TagBoxField.type_key == type_key,
            #                            )
            #                        )
            #                    )
            #                )
            #
            #                return set(tags) if tags else None
            #            else:
            return value if value else None

        def sanitize_json_field(value):
            if isinstance(value, list):
                return set(value) if value else None
            else:
                return value if value else None

        with Session(self.sql_lib.engine) as session:
            for json_entry in self.json_lib.entries:
                sql_fields: list[tuple] = []
                json_fields: list[tuple] = []

                sql_entry: Entry = session.scalar(
                    select(Entry).where(Entry.id == json_entry.id + 1)
                )
                if not sql_entry:
                    logger.info(
                        "[Field Comparison]",
                        message=f"NEW  (SQL): SQL Entry ID mismatch: {json_entry.id+1}",
                    )
                    self.discrepancies.append(
                        f"[Field Comparison]:\nNEW (SQL): SQL Entry ID not found: {json_entry.id+1}"
                    )
                    self.field_parity = False
                    return self.field_parity

                for sf in sql_entry.fields:
                    if sf.type.type.value not in {6, 7, 8}:
                        sql_fields.append(
                            (
                                sql_entry.id,
                                sf.type.key,
                                sanitize_field(
                                    session, sql_entry, sf.value, sf.type.type, sf.type_key
                                ),
                            )
                        )
                sql_fields.sort()

                # NOTE: The JSON database allowed for separate tag fields of the same type with
                # different values. The SQL database does not, and instead merges these values
                # across all instances of that field on an entry.
                # TODO: ROADMAP: "Tag Categories" will merge all field tags onto the entry.
                # All visual separation from there will be data-driven from the tag itself.
                # meta_tags_count: int = 0
                # content_tags_count: int = 0
                tags_count: int = 0
                # merged_meta_tags: set[int] = set()
                # merged_content_tags: set[int] = set()
                merged_tags: set[int] = set()
                for jf in json_entry.fields:
                    int_key: int = list(jf.keys())[0]
                    value = sanitize_json_field(list(jf.values())[0])
                    if int_key in {6, 7, 8}:
                        tags_count += 1
                        merged_tags = merged_tags.union(value or [])
                        pass
                    else:
                        key: str = self.sql_lib.get_field_name_from_id(int_key).name
                        json_fields.append((json_entry.id + 1, key, value))

                # TODO: DO NOT IGNORE TAGS
                # if meta_tags_count:
                #     for _ in range(0, meta_tags_count):
                #         json_fields.append(
                #             (
                #                 json_entry.id + 1,
                #                 _FieldID.TAGS_META.name,
                #                 merged_meta_tags if merged_meta_tags else None,
                #             )
                #         )
                # if content_tags_count:
                #     for _ in range(0, content_tags_count):
                #         json_fields.append(
                #             (
                #                 json_entry.id + 1,
                #                 _FieldID.TAGS_CONTENT.name,
                #                 merged_content_tags if merged_content_tags else None,
                #             )
                #         )
                # if tags_count:
                #     for _ in range(0, tags_count):
                #         json_fields.append(
                #             (
                #                 json_entry.id + 1,
                #                 "TAGS",
                #                 merged_tags if merged_tags else None,
                #             )
                #         )
                json_fields.sort()

                if not (
                    json_fields is not None
                    and sql_fields is not None
                    and (json_fields == sql_fields)
                ):
                    self.discrepancies.append(
                        f"[Field Comparison]:\nOLD (JSON):{json_fields}\nNEW  (SQL):{sql_fields}"
                    )
                    self.field_parity = False
                    return self.field_parity

                logger.info(
                    "[Field Comparison]",
                    fields="\n".join([str(x) for x in zip(json_fields, sql_fields)]),
                )

        self.field_parity = True
        return self.field_parity

    def check_path_parity(self) -> bool:
        """Check if all JSON file paths match the new SQL paths."""
        with Session(self.sql_lib.engine) as session:
            json_paths: list = sorted([x.path / x.filename for x in self.json_lib.entries])
            sql_paths: list = sorted(list(session.scalars(select(Entry.path))))
        self.path_parity = (
            json_paths is not None and sql_paths is not None and (json_paths == sql_paths)
        )
        return self.path_parity

    def check_subtag_parity(self) -> bool:
        """Check if all JSON subtags match the new SQL subtags."""
        sql_subtags: set[int] = None
        json_subtags: set[int] = None

        with Session(self.sql_lib.engine) as session:
            for tag in self.sql_lib.tags:
                if tag.id in range(0, 1000):
                    break
                tag_id = tag.id  # Tag IDs start at 0
                sql_subtags = set(
                    session.scalars(select(TagSubtag.child_id).where(TagSubtag.parent_id == tag.id))
                )
                # sql_subtags = sql_subtags.difference([x for x in range(0, 1000)])

                # JSON tags allowed self-parenting; SQL tags no longer allow this.
                json_subtags = set(self.json_lib.get_tag(tag_id).subtag_ids)
                json_subtags.discard(tag_id)

                logger.info(
                    "[Subtag Parity]",
                    tag_id=tag_id,
                    json_subtags=json_subtags,
                    sql_subtags=sql_subtags,
                )

                if not (
                    sql_subtags is not None
                    and json_subtags is not None
                    and (sql_subtags == json_subtags)
                ):
                    self.discrepancies.append(
                        f"[Subtag Parity][Tag ID: {tag_id}]:"
                        f"\nOLD (JSON):{json_subtags}\nNEW (SQL):{sql_subtags}"
                    )
                    self.subtag_parity = False
                    return self.subtag_parity

        self.subtag_parity = True
        return self.subtag_parity

    def check_ext_type(self) -> bool:
        return self.json_lib.is_exclude_list == self.sql_lib.prefs(LibraryPrefs.IS_EXCLUDE_LIST)

    def check_alias_parity(self) -> bool:
        """Check if all JSON aliases match the new SQL aliases."""
        sql_aliases: set[str] = None
        json_aliases: set[str] = None

        with Session(self.sql_lib.engine) as session:
            for tag in self.sql_lib.tags:
                if tag.id in range(0, 1000):
                    break
                tag_id = tag.id  # Tag IDs start at 0
                sql_aliases = set(
                    session.scalars(select(TagAlias.name).where(TagAlias.tag_id == tag.id))
                )
                json_aliases = set([x for x in self.json_lib.get_tag(tag_id).aliases if x])

                logger.info(
                    "[Alias Parity]",
                    tag_id=tag_id,
                    json_aliases=json_aliases,
                    sql_aliases=sql_aliases,
                )
                if not (
                    sql_aliases is not None
                    and json_aliases is not None
                    and (sql_aliases == json_aliases)
                ):
                    self.discrepancies.append(
                        f"[Alias Parity][Tag ID: {tag_id}]:"
                        f"\nOLD (JSON):{json_aliases}\nNEW (SQL):{sql_aliases}"
                    )
                    self.alias_parity = False
                    return self.alias_parity

        self.alias_parity = True
        return self.alias_parity

    def check_shorthand_parity(self) -> bool:
        """Check if all JSON shorthands match the new SQL shorthands."""
        sql_shorthand: str = None
        json_shorthand: str = None

        for tag in self.sql_lib.tags:
            if tag.id in range(0, 1000):
                break
            tag_id = tag.id  # Tag IDs start at 0
            sql_shorthand = tag.shorthand
            json_shorthand = self.json_lib.get_tag(tag_id).shorthand

            logger.info(
                "[Shorthand Parity]",
                tag_id=tag_id,
                json_shorthand=json_shorthand,
                sql_shorthand=sql_shorthand,
            )

            if not (
                sql_shorthand is not None
                and json_shorthand is not None
                and (sql_shorthand == json_shorthand)
            ):
                self.discrepancies.append(
                    f"[Shorthand Parity][Tag ID: {tag_id}]:"
                    f"\nOLD (JSON):{json_shorthand}\nNEW (SQL):{sql_shorthand}"
                )
                self.shorthand_parity = False
                return self.shorthand_parity

        self.shorthand_parity = True
        return self.shorthand_parity

    def check_color_parity(self) -> bool:
        """Check if all JSON tag colors match the new SQL tag colors."""
        sql_color: str = None
        json_color: str = None

        for tag in self.sql_lib.tags:
            if tag.id in range(0, 1000):
                break
            tag_id = tag.id  # Tag IDs start at 0
            sql_color = tag.color.name
            json_color = (
                TagColor.get_color_from_str(self.json_lib.get_tag(tag_id).color).name
                if (self.json_lib.get_tag(tag_id).color) != ""
                else TagColor.DEFAULT.name
            )

            logger.info(
                "[Color Parity]",
                tag_id=tag_id,
                json_color=json_color,
                sql_color=sql_color,
            )

            if not (sql_color is not None and json_color is not None and (sql_color == json_color)):
                self.discrepancies.append(
                    f"[Color Parity][Tag ID: {tag_id}]:"
                    f"\nOLD (JSON):{json_color}\nNEW (SQL):{sql_color}"
                )
                self.color_parity = False
                return self.color_parity

        self.color_parity = True
        return self.color_parity
