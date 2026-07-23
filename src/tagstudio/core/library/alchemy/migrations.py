# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path

import sqlalchemy
import structlog
import ujson
from sqlalchemy import (
    Engine,
    and_,
    delete,
    select,
    text,
    update,
)
from sqlalchemy.orm import (
    Session,
)

from tagstudio.core.constants import (
    IGNORE_NAME,
    TAG_ARCHIVED,
    TS_FOLDER_NAME,
)
from tagstudio.core.library.alchemy import default_color_groups
from tagstudio.core.library.alchemy.constants import (
    DB_VERSION,
    DB_VERSION_CURRENT_KEY,
    DB_VERSION_INITIAL_KEY,
    DEFAULT_FIELD_TEMPLATES,
)
from tagstudio.core.library.alchemy.fields import (
    LEGACY_FIELD_MAP,
    DatetimeField,
    TextField,
)
from tagstudio.core.library.alchemy.joins import TagParent
from tagstudio.core.library.alchemy.models import (
    Tag,
    TagColorGroup,
    Version,
)
from tagstudio.core.library.ignore import migrate_ext_list
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.translations import Translations

logger = structlog.get_logger(__name__)


class MigrationError(Exception):
    pass


class DBMigrations:
    def __init__(self, library_dir: Path, engine: Engine) -> None:
        self.library_dir = library_dir
        self.engine = engine

        # Don't check DB version when creating new library
        self.loaded_db_version = self.__get_version(DB_VERSION_CURRENT_KEY)
        self.initial_db_version = self.__get_version(DB_VERSION_INITIAL_KEY)

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

        logger.info(f"[Library] Library DB version: {self.loaded_db_version}")

        raise NotImplementedError

    @property
    def required(self) -> bool:
        return self.loaded_db_version < DB_VERSION

    def run(self):
        # migrate DB step by step from one version to the next
        # (migration_method, db_version, initial_db_version)
        migrations = [
            (self.__apply_db7_migration, 7, None),  # changes: value_type, tags
            (self.__apply_db8_migration, 8, None),  # changes: tag_colors
            (self.__apply_db9_migration, 9, None),  # changes: entries
            (self.__apply_db100_migration, 100, None),  # changes: tag_parents
            (self.__apply_db101_migration, 101, None),  # changes: versions
            (self.__apply_db102_migration, 102, None),  # changes: tag_parents
            (self.__apply_db103_migration, 103, None),  # changes: tags
            (self.__apply_db104_migration, 104, None),  # changes: deletes preferences
            (self.__apply_db200_migration, 200, None),  # changes: field tables
            (self.__apply_db201_migration, 201, 200),  # changes: field tables
            (self.__apply_db202_migration, 202, None),  # changes: tag_parents
            (self.__apply_db300_migration, 300, None),  # changes: deletes folders
        ]
        for migration, v, iv in migrations:
            if self.loaded_db_version < v and (iv is None or self.initial_db_version < iv):
                logger.info(f"[Library][Migration][{v}] Starting DB Migration")
                with Session(self.engine) as session:
                    # any error causes transaction to rollback
                    migration(session, self.library_dir)
                    self.loaded_db_version = v
                    self.__set_version(session, DB_VERSION_CURRENT_KEY, v)
                    session.commit()
                logger.info(f"[Library][Migration][{v}] Completed DB Migration")

        assert self.loaded_db_version >= DB_VERSION, (
            "Ran all migrations, but the DB is still not on the newest version"
        )
        logger.info(f"[Library] Library migrated to DB version {DB_VERSION}")

    def __get_version(self, key: str) -> int:
        """Get a version value from the DB.

        Args:
            key(str): The key for the name of the version type to set.
        """
        with Session(self.engine) as session:
            engine = sqlalchemy.inspect(self.engine)
            try:
                # "Version" table added in DB_VERSION 101
                if engine and engine.has_table("versions"):
                    version = session.scalar(select(Version).where(Version.key == key))
                    assert version
                    return version.value
                # NOTE: The "Preferences" table has been depreciated as of TagStudio 9.5.4
                # and is set to be removed in a future release.
                else:
                    return int(
                        unwrap(
                            session.scalar(
                                text("SELECT value FROM preferences WHERE key == 'DB_VERSION'")
                            )
                        )
                    )
            except Exception:
                return 0

    def __set_version(self, session: Session, key: str, value: int) -> None:
        """Set a version value to the DB.

        Args:
            session(Session): The SQLAlchemy DB Session to use.
            key(str): The key for the name of the version type to set.
            value(int): The version value to set.
        """
        # Insert if key has no value yet, otherwise update the value
        session.merge(Version(key=key, value=value))

    def __apply_db7_migration(self, session: Session, _library_dir: Path):
        """Migrate DB from DB_VERSION 6 to 7."""
        logger.info("[Library][Migration][7] Applying patches to DB_VERSION: 6 library...")
        # Repair tags that may have a disambiguation_id pointing towards a deleted tag.
        # TODO: combine into single sql statement
        all_tag_ids = session.scalars(text("SELECT DISTINCT id FROM tags")).all()
        disam_stmt = (
            update(Tag)
            .where(Tag.disambiguation_id.not_in(all_tag_ids))
            .values(disambiguation_id=None)
        )
        session.execute(disam_stmt)
        session.flush()

    def __apply_db8_migration(self, session: Session, library_dir: Path):
        """Migrate DB from DB_VERSION 7 to 8."""
        # Add the missing color_border column to the TagColorGroups table.
        session.execute(
            text("ALTER TABLE tag_colors ADD COLUMN color_border BOOLEAN DEFAULT FALSE NOT NULL")
        )
        session.flush()
        logger.info("[Library][Migration][8] Added color_border column to tag_colors table")

        # collect new default tag colors
        tag_colors: list[TagColorGroup] = [
            color
            for color in default_color_groups.shades()
            if color.slug in ["burgundy", "dark-teal", "dark_lavender"]
        ]

        # Add any new default colors introduced in DB_VERSION 8
        for color in tag_colors:
            session.add(color)
        session.flush()
        logger.info(
            "[Library][Migration][8] Migrated tag colors to DB_VERSION 8+",
            color_name=tag_colors,
        )

        # Update Neon colors to use the the color_border property
        for color in default_color_groups.neon():
            neon_stmt = (
                update(TagColorGroup)
                .where(
                    and_(
                        TagColorGroup.namespace == color.namespace,
                        TagColorGroup.slug == color.slug,
                    )
                )
                .values(
                    slug=color.slug,
                    namespace=color.namespace,
                    name=color.name,
                    primary=color.primary,
                    secondary=color.secondary,
                    color_border=color.color_border,
                )
            )
            session.execute(neon_stmt)
        session.flush()

    def __apply_db9_migration(self, session: Session, library_dir: Path):
        """Migrate DB from DB_VERSION 8 to 9."""
        # Apply database schema changes
        add_filename_column = text(
            "ALTER TABLE entries ADD COLUMN filename TEXT NOT NULL DEFAULT ''"
        )
        session.execute(add_filename_column)
        session.flush()
        logger.info("[Library][Migration][9] Added filename column to entries table")

        # Populate the new filename column.
        from tagstudio.core.library.alchemy.library import Library

        for entry in Library._all_entries(session):
            entry.filename = entry.path.name
            session.merge(entry)
        session.flush()
        logger.info("[Library][Migration][9] Populated filename column in entries table")

    def __apply_db100_migration(self, session: Session, library_dir: Path):
        """Migrate DB to DB_VERSION 100."""
        # Repair parent-child tag relationships that are the wrong way around.
        stmt = update(TagParent).values(
            parent_id=TagParent.child_id,
            child_id=TagParent.parent_id,
        )
        session.execute(stmt)
        session.flush()
        logger.info("[Library][Migration][100] Refactored TagParent table")

    def __apply_db101_migration(self, session: Session, library_dir: Path):
        """Migrate DB to DB_VERSION 101."""
        # Create versions table
        session.execute(
            text("""
        CREATE TABLE versions (
            "key" VARCHAR NOT NULL PRIMARY KEY,
            value INTEGER NOT NULL,
        );
        """)
        )
        session.flush()
        # Ensure version rows are present
        session.add(Version(key=DB_VERSION_INITIAL_KEY, value=100))
        session.flush()

    def __apply_db102_migration(self, session: Session, library_dir: Path):
        """Migrate DB to DB_VERSION 102."""
        # delete TagParents with a dangling parent reference
        stmt = delete(TagParent).where(TagParent.parent_id.not_in(select(Tag.id).distinct()))
        session.execute(stmt)
        session.flush()
        logger.info("[Library][Migration][102] Verified TagParent table data")

    def __apply_db103_migration(self, session: Session, library_dir: Path):
        """Migrate DB from DB_VERSION 102 to 103."""
        # add the new hidden column for tags
        session.execute(text("ALTER TABLE tags ADD COLUMN is_hidden BOOLEAN NOT NULL DEFAULT 0"))
        session.flush()
        logger.info("[Library][Migration][103] Added is_hidden column to tags table")

        # mark the "Archived" tag as hidden
        session.query(Tag).filter(Tag.id == TAG_ARCHIVED).update({"is_hidden": True})
        session.flush()
        logger.info("[Library][Migration][103] Updated archived tag to be hidden")

    def __apply_db104_migration(self, session: Session, library_dir: Path):
        """Migrate DB from DB_VERSION 103 to 104."""
        # Convert file extension list to ts_ignore file, if a .ts_ignore file does not exist
        self.__migrate_sql_to_ts_ignore(session, library_dir)
        session.execute(text("DROP TABLE preferences"))
        session.flush()

    def __migrate_sql_to_ts_ignore(self, session: Session, library_dir: Path):
        # Do not continue if existing '.ts_ignore' file is found
        ts_ignore = library_dir / TS_FOLDER_NAME / IGNORE_NAME
        if Path(ts_ignore).exists():
            return

        # Load legacy extension data
        extensions: list[str] = ujson.loads(
            unwrap(
                session.scalar(text("SELECT value FROM preferences WHERE key = 'EXTENSION_LIST'"))
            )
        )
        is_exclude_list: bool = unwrap(
            session.scalar(text("SELECT value FROM preferences WHERE key = 'IS_EXCLUDE_LIST'"))
        )

        with open(ts_ignore, "w") as f:
            f.write(migrate_ext_list(extensions, is_exclude_list))

    def __apply_db200_migration(self, session: Session, library_dir: Path):
        """Migrate DB to DB_VERSION 200."""
        # Drop unused 'boolean_fields' and 'value_type' tables
        logger.info("[Library][Migration][200] Dropping boolean_fields and value_type tables...")
        session.execute(text("DROP TABLE boolean_fields"))
        session.execute(text("DROP TABLE value_type"))

        # Add 'name' column to text_fields and datetime_fields tables
        logger.info("[Library][Migration][200] Adding name columns to field tables...")
        stmt = text('ALTER TABLE text_fields ADD COLUMN name VARCHAR DEFAULT ""')
        session.execute(stmt)
        stmt = text('ALTER TABLE datetime_fields ADD COLUMN name VARCHAR DEFAULT ""')
        session.execute(stmt)

        # Drop unnecessary 'position' columns
        logger.info("[Library][Migration][200] Dropping position columns to field tables...")
        session.execute(text("ALTER TABLE datetime_fields DROP COLUMN position"))
        session.execute(text("ALTER TABLE text_fields DROP COLUMN position"))

        # Add 'is_multiline' column to text_fields table
        logger.info("[Library][Migration][200] Adding is_multiline column to text_fields...")
        stmt = text("ALTER TABLE text_fields ADD COLUMN is_multiline BOOLEAN NOT NULL DEFAULT 0")
        session.execute(stmt)
        session.flush()

        # Move values from old `type_key` columns into new `name` columns
        logger.info("[Library][Migration][200] Moving values from type_key columns to name...")
        session.execute(text("UPDATE text_fields SET name = type_key"))
        session.execute(text("UPDATE datetime_fields SET name = type_key"))
        session.flush()

        # Change `name` values to title case
        logger.info("[Library][Migration][200] Normalizing TextField names...")
        for text_field in session.execute(select(TextField)).scalars():
            # NOTE: The only exception to the "Title Case" conversion is the "URL" field.
            text_field.name = text_field.name.title().replace("Url", "URL").replace("_", " ")
        logger.info("[Library][Migration][200] Normalizing DatetimeField names...")
        for datetime_field in session.execute(select(DatetimeField)).scalars():
            datetime_field.name = datetime_field.name.title().replace("_", " ")
        session.flush()

        # Add correct `is_multiline` values to text_fields table
        logger.info("[Library][Migration][200] Updating is_multiline for legacy TEXT_BOXes...")
        text_boxes = [
            x.get("name") for x in LEGACY_FIELD_MAP.values() if x.get("is_multiline") is True
        ]
        update_stmt = (
            update(TextField).where(TextField.name.in_(text_boxes)).values(is_multiline=True)
        )
        session.execute(update_stmt)
        session.flush()

        # Repair legacy "Description" fields to use is_multiline = True
        logger.info("[Library][Migration][200] Repairing legacy Description fields...")
        desc_stmt = (
            update(TextField)
            .where(TextField.name == "Description" and TextField.is_multiline == False)  # noqa: E712
            .values(is_multiline=True)
        )
        session.execute(desc_stmt)

        # Repair legacy "Comments" fields to use is_multiline = True
        logger.info("[Library][Migration][200] Repairing legacy Comment fields...")
        comm_stmt = (
            update(TextField)
            .where(TextField.name == "Comments" and TextField.is_multiline == False)  # noqa: E712
            .values(is_multiline=True)
        )
        session.execute(comm_stmt)

        # Add default field templates
        logger.info("[Library][Migration][200] Adding default field templates...")
        for template in DEFAULT_FIELD_TEMPLATES:
            session.add(template)
        session.flush()

        # DB indices for improved performance
        session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_tags_name_shorthand ON tags (name, shorthand)")
        )
        session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_tag_parents_child_id ON tag_parents (child_id)")
        )
        session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_tag_entries_entry_id ON tag_entries (entry_id)")
        )

    def __apply_db201_migration(self, session: Session, library_dir: Path):
        """Migrate DB to DB_VERSION 201."""
        create_text_fields_table = text("""
        CREATE TABLE text_fields_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            name VARCHAR NOT NULL,
            entry_id INTEGER NOT NULL,
            value VARCHAR,
            is_multiline BOOLEAN NOT NULL,
            FOREIGN KEY(entry_id) REFERENCES entries (id)
        )
        """)
        create_datetime_fields_table = text("""
        CREATE TABLE datetime_fields_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            name VARCHAR NOT NULL,
            entry_id INTEGER NOT NULL,
            value VARCHAR,
            FOREIGN KEY(entry_id) REFERENCES entries (id)
        )
        """)

        logger.info("[Library][Migration][201] Dropping type_key from text_fields table...")
        session.execute(create_text_fields_table)
        session.flush()
        session.execute(
            text("""
                INSERT INTO text_fields_new (id, name, entry_id, value, is_multiline)
                SELECT id, name, entry_id, value, is_multiline
                FROM text_fields
            """)
        )
        session.execute(text("DROP TABLE text_fields"))
        session.execute(text("ALTER TABLE text_fields_new RENAME TO text_fields"))

        logger.info("[Library][Migration][201] Dropping type_key from datetime_fields table...")
        session.execute(create_datetime_fields_table)
        session.flush()
        session.execute(
            text("""
                INSERT INTO datetime_fields_new (id, name, entry_id, value)
                SELECT id, name, entry_id, value
                FROM datetime_fields
            """)
        )
        session.execute(text("DROP TABLE datetime_fields"))
        session.execute(text("ALTER TABLE datetime_fields_new RENAME TO datetime_fields"))

        session.flush()

    def __apply_db202_migration(self, session: Session, library_dir: Path):
        """Migrate DB to DB_VERSION 202."""
        stmt = delete(TagParent).where(TagParent.child_id.not_in(select(Tag.id).distinct()))
        session.execute(stmt)
        session.flush()
        logger.info("[Library][Migration][202] Verified TagParent table data")

    def __apply_db300_migration(self, session: Session, library_dir: Path):
        ## remove folder_id column from entries table
        # create new table in the desired scheme (without folder_id column)
        session.execute(
            text("""
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
        )
        session.flush()
        # transfer data to new table
        session.execute(
            text("""
            INSERT INTO entries_new (id, path, suffix, date_created, date_modified, date_added,
                                     filename)
            SELECT id, path, suffix, date_created, date_modified, date_added, filename
            FROM entries
        """)
        )
        # delete old table
        session.execute(text("DROP TABLE entries"))
        # rename new table to old table
        session.execute(text("ALTER TABLE entries_new RENAME TO entries"))
        session.flush()

        ## drop table "folders"
        session.execute(text("DROP TABLE folders"))
        session.flush()
