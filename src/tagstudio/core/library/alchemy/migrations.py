# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import sqlite3
from collections.abc import Callable
from pathlib import Path
from sqlite3 import Connection
from typing import override

import structlog
import ujson
from sqlalchemy import text
from sqlalchemy.orm import Session

from tagstudio.core.constants import IGNORE_NAME, TAG_ARCHIVED, TS_FOLDER_NAME
from tagstudio.core.library.alchemy import default_color_groups
from tagstudio.core.library.alchemy.constants import (
    DB_VERSION,
    DB_VERSION_CURRENT_KEY,
    DB_VERSION_INITIAL_KEY,
    DEFAULT_DATETIME_FIELD_TEMPLATES,
    DEFAULT_TEXT_FIELD_TEMPLATES,
)
from tagstudio.core.library.alchemy.fields import LEGACY_FIELD_MAP
from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.core.library.alchemy.utils import list_tables
from tagstudio.core.library.ignore import migrate_ext_list
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations

logger = structlog.get_logger(__name__)

LoggingMethod = Callable[[str], str]


class MigrationError(Exception):
    pass


class DBMigration:
    version: int
    initial_version: int | None = None

    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError


class DBMigrations:
    def __init__(self, library_dir: Path, sql_filename: str) -> None:
        self.library_dir = library_dir
        self._connection = sqlite3.connect(
            str(library_dir / TS_FOLDER_NAME / sql_filename), autocommit=False
        )

        # Don't check DB version when creating new library
        self.loaded_db_version = self._get_version(DB_VERSION_CURRENT_KEY)
        self.initial_db_version = self._get_version(DB_VERSION_INITIAL_KEY)

        # ======================== Library Database Version Checking =======================
        # DB_VERSION 6 is the first supported SQLite DB version.
        # If the DB_VERSION is >= 100, that means it's a compound major + minor version.
        #   - Dividing by 100 and flooring gives the major (breaking changes) version.
        #   - If a DB has major version higher than the current program, don't load it.
        #   - If only the minor version is higher, it's still allowed to load.
        if self.loaded_db_version < 6 or (
            self.loaded_db_version >= 100 and self.loaded_db_version // 100 > DB_VERSION // 100
        ):
            mismatch_text = Translations["status.library_version_mismatch"]
            found_text = Translations["status.library_version_found"]
            expected_text = Translations["status.library_version_expected"]
            raise MigrationError(
                f"{mismatch_text}\n"
                f"{found_text} v{self.loaded_db_version}, "
                f"{expected_text} v{DB_VERSION}"
            )

        logger.info(
            f"[Library][Migration] "
            f"Opening Library with DB Version {self.loaded_db_version}/{DB_VERSION}"
        )

    @property
    def required(self) -> bool:
        return self.loaded_db_version < DB_VERSION

    def run(self):
        if not self.required:
            return

        # migrate DB step by step from one version to the next
        # (migration_method, db_version, initial_db_version)
        migrations: list[type[DBMigration]] = [
            MigrationTo7,  # changes: value_type, tags
            MigrationTo8,  # changes: tag_colors
            MigrationTo9,  # changes: entries
            MigrationTo100,  # changes: tag_parents
            MigrationTo101,  # changes: versions
            MigrationTo102,  # changes: tag_parents
            MigrationTo103,  # changes: tags
            MigrationTo104,  # changes: deletes preferences
            MigrationTo200,  # changes: field tables
            MigrationTo201,  # changes: field tables
            MigrationTo202,  # changes: tag_parents
            MigrationTo300,  # changes: deletes folders
            MigrationTo400,  # changes: add category_exclusions
        ]
        for migration in migrations:
            if self.loaded_db_version < migration.version and (
                migration.initial_version is None
                or self.initial_db_version < migration.initial_version
            ):
                logger.info(f"[Library][Migration][{migration.version}] Starting DB Migration")
                # any error causes transaction to rollback
                migration.run(
                    self._connection,
                    self.library_dir,
                    lambda msg, v=migration.version: f"[Library][Migration][{v}] {msg}",
                )
                self.loaded_db_version = migration.version
                try:
                    self._set_version(DB_VERSION_CURRENT_KEY, migration.version)
                    logger.info(f"[Library][Migration][{migration.version}] Completed DB Migration")
                except Exception as e:
                    logger.info(
                        f"[Library][Migration][{migration.version}] "
                        "Couldn't update version, continuing without commit",
                        error=e,
                    )
                else:
                    self._connection.commit()

        assert self.loaded_db_version >= DB_VERSION, (
            "Ran all migrations, but the DB is still not on the newest version"
        )

    def _get_version(self, key: str) -> int:
        """Get a version value from the DB.

        Args:
            key(str): The name of the version type to retrieve.
        """
        # "Version" table added in DB_VERSION 101
        if "versions" in list_tables(self._connection):
            query = ("SELECT value FROM versions WHERE key == ?", [key])
        # "Preferences" table deprecated in TagStudio 9.5.4
        else:
            query = ("SELECT value FROM preferences WHERE key == 'DB_VERSION'", [])

        return int(unwrap(self._connection.execute(*query).fetchone())[0])

    def _set_version(self, key: str, value: int) -> None:
        """Set a version value to the DB.

        Args:
            key(str): The the name of the version type to set.
            value(int): The version value to set.
        """
        # Insert if key has no value yet, otherwise update the value
        self._connection.execute(
            "INSERT INTO versions (key, value) VALUES (?, ?)"
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            [key, value],
        )


class MigrationTo7(DBMigration):
    version = 7

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB from DB_VERSION 6 to 7."""
        logger.info(fmt_log("Applying patches to DB_VERSION: 6 library..."))
        # Repair tags that may have a disambiguation_id pointing towards a deleted tag.
        conn.execute(
            "UPDATE tags "
            "SET disambiguation_id = null "
            "WHERE NOT disambiguation_id IN ("
            "SELECT id FROM tags"
            ")"
        )


class MigrationTo8(DBMigration):
    version = 8

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB from DB_VERSION 7 to 8."""
        # Add the missing color_border column to the TagColorGroups table.
        # TODO: as before, this migration uses the current default colors, while it should really be
        # using the default colors as they were in that specific version.
        # FUTURE CHANGES TO THE DEFAULT COLORS WILL BREAK THIS
        conn.execute(
            "ALTER TABLE tag_colors ADD COLUMN color_border BOOLEAN DEFAULT FALSE NOT NULL"
        )
        logger.info(fmt_log("Added color_border column to tag_colors table"))

        # collect new default tag colors
        tag_colors: list[TagColorGroup] = [
            color
            for color in default_color_groups.shades()
            if color.slug in ["burgundy", "dark-teal", "dark_lavender"]
        ]

        # Add any new default colors introduced in DB_VERSION 8
        for color in tag_colors:
            conn.execute(
                'INSERT INTO tag_colors (slug, namespace, name, "primary", secondary) '
                "VALUES (?, ?, ?, ?, ?)",
                [color.slug, color.namespace, color.name, color.primary, color.secondary],
            )
        logger.info(
            fmt_log("Migrated tag colors to DB_VERSION 8+"),
            color_name=tag_colors,
        )

        # Update Neon colors to use the the color_border property
        for color in default_color_groups.neon():
            conn.execute(
                "UPDATE tag_colors"
                "SET slug = ?, namespace = ?, name = ?, "
                '"primary" = ?, secondary = ?, color_border = ? '
                "WHERE namespace == ? AND slug = ?",
                [
                    color.slug,
                    color.namespace,
                    color.name,
                    color.primary,
                    color.secondary,
                    color.color_border,
                    color.namespace,
                    color.slug,
                ],
            )


class MigrationTo9(DBMigration):
    version = 9

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB from DB_VERSION 8 to 9."""
        # Apply database schema changes
        conn.execute("ALTER TABLE entries ADD COLUMN filename TEXT NOT NULL DEFAULT ''")
        logger.info(fmt_log("Added filename column to entries table"))

        # Populate the new filename column.
        paths = [
            (id, Path(path_str))
            for id, path_str in conn.execute("SELECT id, path FROM entries").fetchall()
        ]
        for eid, path in paths:
            conn.execute("UPDATE entries SET filename = ? WHERE id = ?", [path.name, eid])
        logger.info(fmt_log("Populated filename column in entries table"))


class MigrationTo100(DBMigration):
    version = 100

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB to DB_VERSION 100."""
        # Repair parent-child tag relationships that are the wrong way around.
        conn.execute("UPDATE tag_parents SET parent_id = child_id, child_id = parent_id")
        logger.info(fmt_log("Refactored TagParent table"))


class MigrationTo101(DBMigration):
    version = 101

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB to DB_VERSION 101."""
        # Create versions table
        conn.execute("""
            CREATE TABLE versions (
                "key" VARCHAR NOT NULL PRIMARY KEY,
                value INTEGER NOT NULL
            )
        """)
        # Ensure version rows are present
        conn.execute(
            'INSERT INTO versions ("key", value) VALUES (?, ?)', [DB_VERSION_INITIAL_KEY, 100]
        )
        logger.info(fmt_log("Created versions table"))


class MigrationTo102(DBMigration):
    version = 102

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB to DB_VERSION 102."""
        # delete TagParents with a dangling parent reference
        conn.execute("""
            DELETE FROM tag_parents
            WHERE NOT parent_id IN (
                SELECT id
                FROM tags
            )
        """)
        logger.info(fmt_log("Verified TagParent table data"))


class MigrationTo103(DBMigration):
    version = 103

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB from DB_VERSION 102 to 103."""
        # add the new hidden column for tags
        conn.execute("ALTER TABLE tags ADD COLUMN is_hidden BOOLEAN NOT NULL DEFAULT 0")
        logger.info(fmt_log("Added is_hidden column to tags table"))

        # mark the "Archived" tag as hidden
        conn.execute("UPDATE tags SET is_hidden = true WHERE id = ?", [TAG_ARCHIVED])
        logger.info(fmt_log("Updated archived tag to be hidden"))


class MigrationTo104(DBMigration):
    version = 104

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB from DB_VERSION 103 to 104."""
        # Convert file extension list to ts_ignore file, if a .ts_ignore file does not exist
        cls.__migrate_sql_to_ts_ignore(conn, library_dir)
        conn.execute("DROP TABLE preferences")

    @classmethod
    def __migrate_sql_to_ts_ignore(cls, conn: Connection, library_dir: Path):
        # Do not continue if existing '.ts_ignore' file is found
        ts_ignore = library_dir / TS_FOLDER_NAME / IGNORE_NAME
        if Path(ts_ignore).exists():
            return

        # Load legacy extension data
        extensions: list[str] = ujson.loads(
            unwrap(
                conn.execute(
                    "SELECT value FROM preferences WHERE key = 'EXTENSION_LIST'"
                ).fetchone()
            )[0]
        )
        is_exclude_list: bool = unwrap(
            conn.execute("""
                SELECT value
                FROM preferences
                WHERE key = 'IS_EXCLUDE_LIST'
            """).fetchone()[0]
        )

        with open(ts_ignore, "w") as f:
            f.write(migrate_ext_list(extensions, is_exclude_list))


class MigrationTo200(DBMigration):
    version = 200

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB to DB_VERSION 200."""
        # TODO: this migration uses default values of the most recent DB version, fix
        # THIS WILL BREAK ONCE THESE DEFAULT VALUES ARE CHANGED!
        # Drop unused 'boolean_fields' and 'value_type' tables
        logger.info(fmt_log("Dropping boolean_fields and value_type tables..."))
        conn.execute("DROP TABLE boolean_fields")
        conn.execute("DROP TABLE value_type")

        # Add 'name' column to text_fields and datetime_fields tables
        logger.info(fmt_log("Adding name columns to field tables..."))
        conn.execute('ALTER TABLE text_fields ADD COLUMN name VARCHAR DEFAULT ""')
        conn.execute('ALTER TABLE datetime_fields ADD COLUMN name VARCHAR DEFAULT ""')

        # Drop unnecessary 'position' columns
        logger.info(fmt_log("Dropping position columns to field tables..."))
        conn.execute("ALTER TABLE datetime_fields DROP COLUMN position")
        conn.execute("ALTER TABLE text_fields DROP COLUMN position")

        # Add 'is_multiline' column to text_fields table
        logger.info(fmt_log("Adding is_multiline column to text_fields..."))
        conn.execute("ALTER TABLE text_fields ADD COLUMN is_multiline BOOLEAN NOT NULL DEFAULT 0")

        # Move values from old `type_key` columns into new `name` columns
        logger.info(fmt_log("Moving values from type_key columns to name..."))
        conn.execute("UPDATE text_fields SET name = type_key")
        conn.execute("UPDATE datetime_fields SET name = type_key")

        # Change `name` values to title case
        logger.info(fmt_log("Normalizing TextField names..."))
        # NOTE: The only exception to the "Title Case" conversion is the "URL" field.
        names = [
            (name.title().replace("Url", "URL").replace("_", " "), id)
            for id, name in conn.execute("SELECT id, name FROM text_fields").fetchall()
        ]
        conn.executemany("UPDATE text_fields SET name = ? WHERE id = ?", names)

        logger.info(fmt_log("Normalizing DatetimeField names..."))
        names = [
            (name.title().replace("_", " "), id)
            for id, name in conn.execute("SELECT id, name FROM datetime_fields").fetchall()
        ]
        conn.executemany("UPDATE datetime_fields SET name = ? WHERE id = ?", names)

        # Add correct `is_multiline` values to text_fields table
        logger.info(fmt_log("Updating is_multiline for legacy TEXT_BOXes..."))
        text_boxes = [
            x.get("name") for x in LEGACY_FIELD_MAP.values() if x.get("is_multiline") is True
        ]
        conn.execute("UPDATE text_fields SET is_multiline = true WHERE name in ?", text_boxes)

        # Repair legacy "Description" and "Comments" fields to use is_multiline = True
        logger.info(fmt_log("Repairing legacy Description and Comments fields..."))
        conn.execute("""
            UPDATE text_fields
            SET is_multiline = true
            WHERE name in ('Description', 'Comments') AND is_multiline = false
        """)

        # Add field templates tables
        conn.execute("""
            CREATE TABLE text_field_templates (
                id INTEGER NOT NULL PRIMARY KEY,
                is_multiline BOOLEAN NOT NULL,
                name VARCHAR NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE datetime_field_templates (
                id INTEGER NOT NULL PRIMARY KEY,
                name VARCHAR NOT NULL
            )
        """)

        # Add default field templates
        logger.info(fmt_log("Adding default field templates..."))
        conn.executemany(
            "INSERT INTO text_field_templates (id, name, is_multiline) VALUES (?, ?, ?)",
            [(t.id, t.name, t.is_multiline) for t in DEFAULT_TEXT_FIELD_TEMPLATES],
        )
        conn.executemany(
            "INSERT INTO datetime_field_templates (id, name) VALUES (?, ?)",
            [(t.id, t.name) for t in DEFAULT_DATETIME_FIELD_TEMPLATES],
        )

        # DB indices for improved performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tags_name_shorthand ON tags (name, shorthand)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tag_parents_child_id ON tag_parents (child_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tag_entries_entry_id ON tag_entries (entry_id)"
        )


class MigrationTo201(DBMigration):
    version = 201
    initial_version = 200

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB to DB_VERSION 201."""
        logger.info(fmt_log("Dropping type_key from text_fields table..."))
        conn.execute("""
            CREATE TABLE text_fields_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                entry_id INTEGER NOT NULL,
                value VARCHAR,
                is_multiline BOOLEAN NOT NULL,
                FOREIGN KEY(entry_id) REFERENCES entries (id)
            )
        """)
        conn.execute("""
            INSERT INTO text_fields_new (id, name, entry_id, value, is_multiline)
            SELECT id, name, entry_id, value, is_multiline
            FROM text_fields
        """)
        conn.execute("DROP TABLE text_fields")
        conn.execute("ALTER TABLE text_fields_new RENAME TO text_fields")

        logger.info(fmt_log("Dropping type_key from datetime_fields table..."))
        conn.execute("""
            CREATE TABLE datetime_fields_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                entry_id INTEGER NOT NULL,
                value VARCHAR,
                FOREIGN KEY(entry_id) REFERENCES entries (id)
            )
        """)
        conn.execute("""
            INSERT INTO datetime_fields_new (id, name, entry_id, value)
            SELECT id, name, entry_id, value
            FROM datetime_fields
        """)
        conn.execute("DROP TABLE datetime_fields")
        conn.execute("ALTER TABLE datetime_fields_new RENAME TO datetime_fields")


class MigrationTo202(DBMigration):
    version = 202

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        """Migrate DB to DB_VERSION 202."""
        conn.execute("""
            DELETE FROM tag_parents
            WHERE NOT child_id IN (
                SELECT id
                FROM tags
            )
        """)
        logger.info(fmt_log("Verified TagParent table data"))


class MigrationTo300(DBMigration):
    version = 300

    @override
    @classmethod
    def run(cls, conn: Connection, library_dir: Path, fmt_log: LoggingMethod):
        # remove folder_id column from entries table
        ## create new table in the desired scheme (without folder_id column)
        conn.execute("""
            CREATE TABLE entries_new (
                id INTEGER NOT NULL,
                path VARCHAR NOT NULL,
                suffix VARCHAR NOT NULL,
                date_created DATETIME,
                date_modified DATETIME,
                date_added DATETIME,
                filename TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (id),
                UNIQUE (path)
            )
        """)

        ## transfer data to new table
        conn.execute("""
            INSERT INTO entries_new (id, path, suffix, date_created, date_modified, date_added,
                                     filename)
            SELECT id, path, suffix, date_created, date_modified, date_added, filename
            FROM entries
        """)

        ## delete old table
        conn.execute("DROP TABLE entries")

        ## rename new table to old table
        conn.execute("ALTER TABLE entries_new RENAME TO entries")

        # drop table "folders"
        conn.execute("DROP TABLE folders")


class MigrationTo400(DBMigration):
    version = 400

    @override
    @classmethod
    def run(cls, session: Session, library_dir: Path, fmt_log):
        logger.info(fmt_log("Creating category_exclusions table..."))
        session.execute(
            text("""
        CREATE TABLE category_exclusions (
            tag_id      INTEGER NOT NULL REFERENCES tags(id),
            category_id INTEGER NOT NULL REFERENCES tags(id),

            PRIMARY KEY (tag_id, category_id)
        )
        """)
        )
        session.flush()
