# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import re
import shutil
import time
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from os import makedirs
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4
from warnings import catch_warnings

import structlog
from humanfriendly import format_timespan
from sqlalchemy import (
    URL,
    ColumnExpressionArgument,
    Engine,
    NullPool,
    ScalarResult,
    and_,
    asc,
    create_engine,
    delete,
    desc,
    exists,
    func,
    or_,
    select,
    text,
    update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    Session,
    contains_eager,
    joinedload,
    make_transient,
    selectinload,
)

from tagstudio.core.constants import (
    BACKUP_FOLDER_NAME,
    LEGACY_TAG_FIELD_IDS,
    RESERVED_NAMESPACE_PREFIX,
    RESERVED_TAG_END,
    RESERVED_TAG_START,
    TAG_ARCHIVED,
    TAG_FAVORITE,
    TAG_META,
    TS_FOLDER_NAME,
)
from tagstudio.core.enums import LibraryPrefs
from tagstudio.core.library.alchemy import default_color_groups
from tagstudio.core.library.alchemy.db import make_tables
from tagstudio.core.library.alchemy.enums import (
    MAX_SQL_VARIABLES,
    BrowsingState,
    FieldTypeEnum,
    SortingModeEnum,
)
from tagstudio.core.library.alchemy.fields import (
    BaseField,
    DatetimeField,
    TextField,
    _FieldID,
)
from tagstudio.core.library.alchemy.joins import TagEntry, TagParent
from tagstudio.core.library.alchemy.models import (
    Entry,
    Folder,
    Namespace,
    Preferences,
    Tag,
    TagAlias,
    TagColorGroup,
    ValueType,
)
from tagstudio.core.library.alchemy.visitors import SQLBoolExpressionBuilder
from tagstudio.core.library.json.library import Library as JsonLibrary
from tagstudio.qt.translations import Translations

if TYPE_CHECKING:
    from sqlalchemy import Select


logger = structlog.get_logger(__name__)

TAG_CHILDREN_QUERY = text("""
-- Note for this entire query that tag_parents.child_id is the parent id and tag_parents.parent_id is the child id due to bad naming
WITH RECURSIVE ChildTags AS (
    SELECT :tag_id AS child_id
    UNION
    SELECT tp.parent_id AS child_id
	FROM tag_parents tp
    INNER JOIN ChildTags c ON tp.child_id = c.child_id
)
SELECT * FROM ChildTags;
""")  # noqa: E501


class ReservedNamespaceError(Exception):
    """Raise during an unauthorized attempt to create or modify a reserved namespace value.

    Reserved namespace prefix: "tagstudio".
    """

    pass


def slugify(input_string: str, allow_reserved: bool = False) -> str:
    # Convert to lowercase and normalize unicode characters
    slug = unicodedata.normalize("NFKD", input_string.lower())

    # Remove non-word characters (except hyphens and spaces)
    slug = re.sub(r"[^\w\s-]", "", slug).strip()

    # Replace spaces with hyphens
    slug = re.sub(r"[-\s]+", "-", slug)

    if not allow_reserved and slug.startswith(RESERVED_NAMESPACE_PREFIX):
        raise ReservedNamespaceError

    return slug


def get_default_tags() -> tuple[Tag, ...]:
    meta_tag = Tag(
        id=TAG_META,
        name="Meta Tags",
        aliases={TagAlias(name="Meta"), TagAlias(name="Meta Tag")},
        is_category=True,
    )
    archive_tag = Tag(
        id=TAG_ARCHIVED,
        name="Archived",
        aliases={TagAlias(name="Archive")},
        parent_tags={meta_tag},
        color_slug="red",
        color_namespace="tagstudio-standard",
    )
    favorite_tag = Tag(
        id=TAG_FAVORITE,
        name="Favorite",
        aliases={
            TagAlias(name="Favorited"),
            TagAlias(name="Favorites"),
        },
        parent_tags={meta_tag},
        color_slug="yellow",
        color_namespace="tagstudio-standard",
    )

    return archive_tag, favorite_tag, meta_tag


# The difference in the number of default JSON tags vs default tags in the current version.
DEFAULT_TAG_DIFF: int = len(get_default_tags()) - len([TAG_ARCHIVED, TAG_FAVORITE])


@dataclass(frozen=True)
class SearchResult:
    """Wrapper for search results.

    Attributes:
        total_count(int): total number of items for given query, might be different than len(items).
        items(list[Entry]): for current page (size matches filter.page_size).
    """

    total_count: int
    items: list[Entry]

    def __bool__(self) -> bool:
        """Boolean evaluation for the wrapper.

        :return: True if there are items in the result.
        """
        return self.total_count > 0

    def __len__(self) -> int:
        """Return the total number of items in the result."""
        return len(self.items)

    def __getitem__(self, index: int) -> Entry:
        """Allow to access items via index directly on the wrapper."""
        return self.items[index]


@dataclass
class LibraryStatus:
    """Keep status of library opening operation."""

    success: bool
    library_path: Path | None = None
    message: str | None = None
    msg_description: str | None = None
    json_migration_req: bool = False


class Library:
    """Class for the Library object, and all CRUD operations made upon it."""

    library_dir: Path | None = None
    storage_path: Path | None
    engine: Engine | None = None
    folder: Folder | None
    included_files: set[Path] = set()

    SQL_FILENAME: str = "ts_library.sqlite"
    JSON_FILENAME: str = "ts_library.json"

    def close(self):
        if self.engine:
            self.engine.dispose()
        self.library_dir: Path | None = None
        self.storage_path = None
        self.folder = None
        self.included_files = set()

    def migrate_json_to_sqlite(self, json_lib: JsonLibrary):
        """Migrate JSON library data to the SQLite database."""
        logger.info("Starting Library Conversion...")
        start_time = time.time()
        folder: Folder = Folder(path=self.library_dir, uuid=str(uuid4()))

        # Tags
        for tag in json_lib.tags:
            color_namespace, color_slug = default_color_groups.json_to_sql_color(tag.color)
            disambiguation_id: int | None = None
            if tag.subtag_ids and tag.subtag_ids[0] != tag.id:
                disambiguation_id = tag.subtag_ids[0]
            self.add_tag(
                Tag(
                    id=tag.id,
                    name=tag.name,
                    shorthand=tag.shorthand,
                    color_namespace=color_namespace,
                    color_slug=color_slug,
                    disambiguation_id=disambiguation_id,
                )
            )
            # Apply user edits to built-in JSON tags.
            if tag.id in range(RESERVED_TAG_START, RESERVED_TAG_END + 1):
                updated_tag = self.get_tag(tag.id)
                if not updated_tag:
                    continue
                updated_tag.name = tag.name
                updated_tag.shorthand = tag.shorthand
                updated_tag.color_namespace = color_namespace
                updated_tag.color_slug = color_slug
                self.update_tag(updated_tag)  # NOTE: This just calls add_tag?

        # Tag Aliases
        for tag in json_lib.tags:
            for alias in tag.aliases:
                if not alias:
                    break
                # Only add new (user-created) aliases to the default tags.
                # This prevents pre-existing built-in aliases from being added as duplicates.
                if tag.id in range(RESERVED_TAG_START, RESERVED_TAG_END + 1):
                    for dt in get_default_tags():
                        if dt.id == tag.id and alias not in dt.alias_strings:
                            self.add_alias(name=alias, tag_id=tag.id)
                else:
                    self.add_alias(name=alias, tag_id=tag.id)

        # Parent Tags (Previously known as "Subtags" in JSON)
        for tag in json_lib.tags:
            for child_id in tag.subtag_ids:
                self.add_parent_tag(parent_id=tag.id, child_id=child_id)

        # Entries
        self.add_entries(
            [
                Entry(
                    path=entry.path / entry.filename,
                    folder=folder,
                    fields=[],
                    id=entry.id + 1,  # JSON IDs start at 0 instead of 1
                    date_added=datetime.now(),
                )
                for entry in json_lib.entries
            ]
        )
        for entry in json_lib.entries:
            for field in entry.fields:
                for k, v in field.items():
                    # Old tag fields get added as tags
                    if k in LEGACY_TAG_FIELD_IDS:
                        self.add_tags_to_entries(entry_ids=entry.id + 1, tag_ids=v)
                    else:
                        self.add_field_to_entry(
                            entry_id=(entry.id + 1),  # JSON IDs start at 0 instead of 1
                            field_id=self.get_field_name_from_id(k),
                            value=v,
                        )

        # Preferences
        self.set_prefs(LibraryPrefs.EXTENSION_LIST, [x.strip(".") for x in json_lib.ext_list])
        self.set_prefs(LibraryPrefs.IS_EXCLUDE_LIST, json_lib.is_exclude_list)

        end_time = time.time()
        logger.info(f"Library Converted! ({format_timespan(end_time - start_time)})")

    def get_field_name_from_id(self, field_id: int) -> _FieldID:
        for f in _FieldID:
            if field_id == f.value.id:
                return f
        return None

    def tag_display_name(self, tag_id: int) -> str:
        with Session(self.engine) as session:
            tag = session.scalar(select(Tag).where(Tag.id == tag_id))
            if not tag:
                return "<NO TAG>"

            if tag.disambiguation_id:
                disam_tag = session.scalar(select(Tag).where(Tag.id == tag.disambiguation_id))
                if not disam_tag:
                    return "<NO DISAM TAG>"
                disam_name = disam_tag.shorthand
                if not disam_name:
                    disam_name = disam_tag.name
                return f"{tag.name} ({disam_name})"
            else:
                return tag.name

    def open_library(self, library_dir: Path, storage_path: Path | None = None) -> LibraryStatus:
        is_new: bool = True
        if storage_path == ":memory:":
            self.storage_path = storage_path
            is_new = True
            return self.open_sqlite_library(library_dir, is_new)
        else:
            self.storage_path = library_dir / TS_FOLDER_NAME / self.SQL_FILENAME
            if self.verify_ts_folder(library_dir) and (is_new := not self.storage_path.exists()):
                json_path = library_dir / TS_FOLDER_NAME / self.JSON_FILENAME
                if json_path.exists():
                    return LibraryStatus(
                        success=False,
                        library_path=library_dir,
                        message="[JSON] Legacy v9.4 library requires conversion to v9.5+",
                        json_migration_req=True,
                    )

        return self.open_sqlite_library(library_dir, is_new)

    def open_sqlite_library(self, library_dir: Path, is_new: bool) -> LibraryStatus:
        connection_string = URL.create(
            drivername="sqlite",
            database=str(self.storage_path),
        )
        # NOTE: File-based databases should use NullPool to create new DB connection in order to
        # keep connections on separate threads, which prevents the DB files from being locked
        # even after a connection has been closed.
        # SingletonThreadPool (the default for :memory:) should still be used for in-memory DBs.
        # More info can be found on the SQLAlchemy docs:
        # https://docs.sqlalchemy.org/en/20/changelog/migration_07.html
        # Under -> sqlite-the-sqlite-dialect-now-uses-nullpool-for-file-based-databases
        poolclass = None if self.storage_path == ":memory:" else NullPool
        db_version: int = 0

        logger.info(
            "[Library] Opening SQLite Library",
            library_dir=library_dir,
            connection_string=connection_string,
        )
        self.engine = create_engine(connection_string, poolclass=poolclass)
        with Session(self.engine) as session:
            # dont check db version when creating new library
            if not is_new:
                db_result = session.scalar(
                    select(Preferences).where(Preferences.key == LibraryPrefs.DB_VERSION.name)
                )
                if db_result:
                    db_version = db_result.value

                # NOTE: DB_VERSION 6 is the first supported SQL DB version.
                if db_version < 6 or db_version > LibraryPrefs.DB_VERSION.default:
                    mismatch_text = Translations["status.library_version_mismatch"]
                    found_text = Translations["status.library_version_found"]
                    expected_text = Translations["status.library_version_expected"]
                    return LibraryStatus(
                        success=False,
                        message=(
                            f"{mismatch_text}\n"
                            f"{found_text} v{db_version}, "
                            f"{expected_text} v{LibraryPrefs.DB_VERSION.default}"
                        ),
                    )

            logger.info(f"[Library] DB_VERSION: {db_version}")
            make_tables(self.engine)

            # Add default tag color namespaces.
            if is_new:
                namespaces = default_color_groups.namespaces()
                try:
                    session.add_all(namespaces)
                    session.commit()
                except IntegrityError as e:
                    logger.error("[Library] Couldn't add default tag color namespaces", error=e)
                    session.rollback()

            # Add default tag colors.
            if is_new:
                tag_colors: list[TagColorGroup] = default_color_groups.standard()
                tag_colors += default_color_groups.pastels()
                tag_colors += default_color_groups.shades()
                tag_colors += default_color_groups.grayscale()
                tag_colors += default_color_groups.earth_tones()
                tag_colors += default_color_groups.neon()
                if is_new:
                    try:
                        session.add_all(tag_colors)
                        session.commit()
                    except IntegrityError as e:
                        logger.error("[Library] Couldn't add default tag colors", error=e)
                        session.rollback()

            # Add default tags.
            if is_new:
                tags = get_default_tags()
                try:
                    session.add_all(tags)
                    session.commit()
                except IntegrityError:
                    session.rollback()

            for pref in LibraryPrefs:
                with catch_warnings(record=True):
                    try:
                        session.add(Preferences(key=pref.name, value=pref.default))
                        session.commit()
                    except IntegrityError:
                        logger.debug("preference already exists", pref=pref)
                        session.rollback()

            for field in _FieldID:
                try:
                    session.add(
                        ValueType(
                            key=field.name,
                            name=field.value.name,
                            type=field.value.type,
                            position=field.value.id,
                            is_default=field.value.is_default,
                        )
                    )
                    session.commit()
                except IntegrityError:
                    logger.debug("ValueType already exists", field=field)
                    session.rollback()

            # check if folder matching current path exists already
            self.folder = session.scalar(select(Folder).where(Folder.path == library_dir))
            if not self.folder:
                folder = Folder(
                    path=library_dir,
                    uuid=str(uuid4()),
                )
                session.add(folder)
                session.expunge(folder)
                session.commit()
                self.folder = folder

            # Apply any post-SQL migration patches.
            if not is_new:
                # save backup if patches will be applied
                if LibraryPrefs.DB_VERSION.default != db_version:
                    self.library_dir = library_dir
                    self.save_library_backup_to_disk()
                    self.library_dir = None

                # schema changes first
                if db_version < 8:
                    self.apply_db8_schema_changes(session)
                if db_version < 9:
                    self.apply_db9_schema_changes(session)

                # now the data changes
                if db_version == 6:
                    self.apply_repairs_for_db6(session)
                if db_version >= 6 and db_version < 8:
                    self.apply_db8_default_data(session)
                if db_version < 9:
                    self.apply_db9_filename_population(session)

            # Update DB_VERSION
            if LibraryPrefs.DB_VERSION.default > db_version:
                self.set_prefs(LibraryPrefs.DB_VERSION, LibraryPrefs.DB_VERSION.default)

        # everything is fine, set the library path
        self.library_dir = library_dir
        return LibraryStatus(success=True, library_path=library_dir)

    def apply_repairs_for_db6(self, session: Session):
        """Apply database repairs introduced in DB_VERSION 7."""
        logger.info("[Library][Migration] Applying patches to DB_VERSION: 6 library...")
        with session:
            # Repair "Description" fields with a TEXT_LINE key instead of a TEXT_BOX key.
            desc_stmd = (
                update(ValueType)
                .where(ValueType.key == _FieldID.DESCRIPTION.name)
                .values(type=FieldTypeEnum.TEXT_BOX.name)
            )
            session.execute(desc_stmd)
            session.flush()

            # Repair tags that may have a disambiguation_id pointing towards a deleted tag.
            all_tag_ids: set[int] = {tag.id for tag in self.tags}
            disam_stmt = (
                update(Tag)
                .where(Tag.disambiguation_id.not_in(all_tag_ids))
                .values(disambiguation_id=None)
            )
            session.execute(disam_stmt)
            session.flush()

            session.commit()

    def apply_db8_schema_changes(self, session: Session):
        """Apply database schema changes introduced in DB_VERSION 8."""
        # TODO: Use Alembic for this part instead
        # Add the missing color_border column to the TagColorGroups table.
        color_border_stmt = text(
            "ALTER TABLE tag_colors ADD COLUMN color_border BOOLEAN DEFAULT FALSE NOT NULL"
        )
        try:
            session.execute(color_border_stmt)
            session.commit()
            logger.info("[Library][Migration] Added color_border column to tag_colors table")
        except Exception as e:
            logger.error(
                "[Library][Migration] Could not create color_border column in tag_colors table!",
                error=e,
            )
            session.rollback()

    def apply_db8_default_data(self, session: Session):
        """Apply default data changes introduced in DB_VERSION 8."""
        tag_colors: list[TagColorGroup] = default_color_groups.standard()
        tag_colors += default_color_groups.pastels()
        tag_colors += default_color_groups.shades()
        tag_colors += default_color_groups.grayscale()
        tag_colors += default_color_groups.earth_tones()
        # tag_colors += default_color_groups.neon() # NOTE: Neon is handled separately

        # Add any new default colors introduced in DB_VERSION 8
        for color in tag_colors:
            try:
                session.add(color)
                logger.info(
                    "[Library][Migration] Migrated tag color to DB_VERSION 8+",
                    color_name=color.name,
                )
                session.commit()
            except IntegrityError:
                session.rollback()

        # Update Neon colors to use the the color_border property
        for color in default_color_groups.neon():
            try:
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
                session.commit()
            except IntegrityError as e:
                logger.error(
                    "[Library] Could not migrate Neon colors to DB_VERSION 8+!",
                    error=e,
                )
                session.rollback()

    def apply_db9_schema_changes(self, session: Session):
        """Apply database schema changes introduced in DB_VERSION 9."""
        add_filename_column = text(
            "ALTER TABLE entries ADD COLUMN filename TEXT NOT NULL DEFAULT ''"
        )
        try:
            session.execute(add_filename_column)
            session.commit()
            logger.info("[Library][Migration] Added filename column to entries table")
        except Exception as e:
            logger.error(
                "[Library][Migration] Could not create filename column in entries table!",
                error=e,
            )
            session.rollback()

    def apply_db9_filename_population(self, session: Session):
        """Populate the filename column introduced in DB_VERSION 9."""
        for entry in self.get_entries():
            session.merge(entry).filename = entry.path.name
        session.commit()
        logger.info("[Library][Migration] Populated filename column in entries table")

    @property
    def default_fields(self) -> list[BaseField]:
        with Session(self.engine) as session:
            types = session.scalars(
                select(ValueType).where(
                    # check if field is default
                    ValueType.is_default.is_(True)
                )
            )
            return [x.as_field for x in types]

    def delete_item(self, item):
        logger.info("deleting item", item=item)
        with Session(self.engine) as session:
            session.delete(item)
            session.commit()

    def get_entry(self, entry_id: int) -> Entry | None:
        """Load entry without joins."""
        with Session(self.engine) as session:
            entry = session.scalar(select(Entry).where(Entry.id == entry_id))
            if not entry:
                return None
            session.expunge(entry)
            make_transient(entry)
            return entry

    def get_entry_full(
        self, entry_id: int, with_fields: bool = True, with_tags: bool = True
    ) -> Entry | None:
        """Load entry and join with all joins and all tags."""
        # NOTE: TODO: Currently this method makes multiple separate queries to the db and combines
        # those into a final Entry object (if using "with" args). This was done due to it being
        # much more efficient than the existing join query, however there likely exists a single
        # query that can accomplish the same task without exhibiting the same slowdown.
        with Session(self.engine) as session:
            tags: set[Tag] | None = None
            tag_stmt: Select[tuple[Tag]]
            entry_stmt = select(Entry).where(Entry.id == entry_id).limit(1)
            if with_fields:
                entry_stmt = (
                    entry_stmt.outerjoin(Entry.text_fields)
                    .outerjoin(Entry.datetime_fields)
                    .options(selectinload(Entry.text_fields), selectinload(Entry.datetime_fields))
                )
            # if with_tags:
            #     entry_stmt = entry_stmt.outerjoin(Entry.tags).options(selectinload(Entry.tags))
            if with_tags:
                tag_stmt = select(Tag).where(
                    and_(
                        TagEntry.tag_id == Tag.id,
                        TagEntry.entry_id == entry_id,
                    )
                )

            start_time = time.time()
            entry = session.scalar(entry_stmt)
            if with_tags:
                tags = set(session.scalars(tag_stmt))  # pyright: ignore [reportPossiblyUnboundVariable]
            end_time = time.time()
            logger.info(
                f"[Library] Time it took to get entry: "
                f"{format_timespan(end_time - start_time, max_units=5)}",
                with_fields=with_fields,
                with_tags=with_tags,
            )
            if not entry:
                return None
            session.expunge(entry)
            make_transient(entry)

            # Recombine the separately queried tags with the base entry object.
            if with_tags and tags:
                entry.tags = tags
            return entry

    def get_entries_full(self, entry_ids: list[int] | set[int]) -> Iterator[Entry]:
        """Load entry and join with all joins and all tags."""
        with Session(self.engine) as session:
            statement = select(Entry).where(Entry.id.in_(set(entry_ids)))
            statement = (
                statement.outerjoin(Entry.text_fields)
                .outerjoin(Entry.datetime_fields)
                .outerjoin(Entry.tags)
            )
            statement = statement.options(
                selectinload(Entry.text_fields),
                selectinload(Entry.datetime_fields),
                selectinload(Entry.tags).options(
                    selectinload(Tag.aliases),
                    selectinload(Tag.parent_tags),
                ),
            )
            statement = statement.distinct()
            entries: ScalarResult[Entry] | list[Entry] = session.execute(statement).scalars()
            entries = entries.unique()  # type: ignore

            entry_order_dict = {e_id: order for order, e_id in enumerate(entry_ids)}
            entries = sorted(entries, key=lambda e: entry_order_dict[e.id])

            for entry in entries:
                yield entry
                session.expunge(entry)

    def get_entry_full_by_path(self, path: Path) -> Entry | None:
        """Get the entry with the corresponding path."""
        with Session(self.engine) as session:
            stmt = select(Entry).where(Entry.path == path)
            stmt = (
                stmt.outerjoin(Entry.text_fields)
                .outerjoin(Entry.datetime_fields)
                .options(selectinload(Entry.text_fields), selectinload(Entry.datetime_fields))
            )
            stmt = (
                stmt.outerjoin(Entry.tags)
                .outerjoin(TagAlias)
                .options(
                    selectinload(Entry.tags).options(
                        joinedload(Tag.aliases),
                        joinedload(Tag.parent_tags),
                    )
                )
            )
            entry = session.scalar(stmt)
            if not entry:
                return None
            session.expunge(entry)
            make_transient(entry)
            return entry

    @property
    def entries_count(self) -> int:
        with Session(self.engine) as session:
            return session.scalar(select(func.count(Entry.id)))

    def get_entries(self, with_joins: bool = False) -> Iterator[Entry]:
        """Load entries without joins."""
        with Session(self.engine) as session:
            stmt = select(Entry)
            if with_joins:
                # load Entry with all joins and all tags
                stmt = (
                    stmt.outerjoin(Entry.text_fields)
                    .outerjoin(Entry.datetime_fields)
                    .outerjoin(Entry.tags)
                )
                stmt = stmt.options(
                    contains_eager(Entry.text_fields),
                    contains_eager(Entry.datetime_fields),
                    contains_eager(Entry.tags),
                )

            stmt = stmt.distinct()

            entries = session.execute(stmt).scalars()
            if with_joins:
                entries = entries.unique()

            for entry in entries:
                yield entry
                session.expunge(entry)

    @property
    def tags(self) -> list[Tag]:
        with Session(self.engine) as session:
            # load all tags and join parent tags
            tags_query = select(Tag).options(selectinload(Tag.parent_tags))
            tags = session.scalars(tags_query).unique()
            tags_list = list(tags)

            for tag in tags_list:
                session.expunge(tag)

        return list(tags_list)

    def verify_ts_folder(self, library_dir: Path) -> bool:
        """Verify/create folders required by TagStudio.

        Returns:
            bool: True if path exists, False if it needed to be created.
        """
        if library_dir is None:
            raise ValueError("No path set.")

        if not library_dir.exists():
            raise ValueError("Invalid library directory.")

        full_ts_path = library_dir / TS_FOLDER_NAME
        if not full_ts_path.exists():
            logger.info("creating library directory", dir=full_ts_path)
            full_ts_path.mkdir(parents=True, exist_ok=True)
            return False
        return True

    def add_entries(self, items: list[Entry]) -> list[int]:
        """Add multiple Entry records to the Library."""
        assert items

        with Session(self.engine) as session:
            # add all items

            try:
                session.add_all(items)
                session.commit()
            except IntegrityError:
                session.rollback()
                logger.error("IntegrityError")
                return []

            new_ids = [item.id for item in items]
            session.expunge_all()

        return new_ids

    def remove_entries(self, entry_ids: list[int]) -> None:
        """Remove Entry items matching supplied IDs from the Library."""
        with Session(self.engine) as session:
            for sub_list in [
                entry_ids[i : i + MAX_SQL_VARIABLES]
                for i in range(0, len(entry_ids), MAX_SQL_VARIABLES)
            ]:
                session.query(Entry).where(Entry.id.in_(sub_list)).delete()
            session.commit()

    def has_path_entry(self, path: Path) -> bool:
        """Check if item with given path is in library already."""
        with Session(self.engine) as session:
            return session.query(exists().where(Entry.path == path)).scalar()

    def get_paths(self, glob: str | None = None, limit: int = -1) -> list[str]:
        path_strings: list[str] = []
        with Session(self.engine) as session:
            if limit > 0:
                paths = session.scalars(select(Entry.path).limit(limit)).unique()
            else:
                paths = session.scalars(select(Entry.path)).unique()
            path_strings = list(map(lambda x: x.as_posix(), paths))
            return path_strings

    def search_library(
        self,
        search: BrowsingState,
        page_size: int,
    ) -> SearchResult:
        """Filter library by search query.

        :return: number of entries matching the query and one page of results.
        """
        assert isinstance(search, BrowsingState)
        assert self.engine

        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Entry)

            if search.ast:
                start_time = time.time()
                statement = statement.where(SQLBoolExpressionBuilder(self).visit(search.ast))
                end_time = time.time()
                logger.info(
                    f"SQL Expression Builder finished ({format_timespan(end_time - start_time)})"
                )

            extensions = self.prefs(LibraryPrefs.EXTENSION_LIST)
            is_exclude_list = self.prefs(LibraryPrefs.IS_EXCLUDE_LIST)

            if extensions and is_exclude_list:
                statement = statement.where(Entry.suffix.notin_(extensions))
            elif extensions:
                statement = statement.where(Entry.suffix.in_(extensions))

            statement = statement.distinct(Entry.id)
            start_time = time.time()
            query_count = select(func.count()).select_from(statement.alias("entries"))
            count_all: int = session.execute(query_count).scalar() or 0
            end_time = time.time()
            logger.info(f"finished counting ({format_timespan(end_time - start_time)})")

            sort_on: ColumnExpressionArgument = Entry.id
            match search.sorting_mode:
                case SortingModeEnum.DATE_ADDED:
                    sort_on = Entry.id
                case SortingModeEnum.FILE_NAME:
                    sort_on = func.lower(Entry.filename)
                case SortingModeEnum.PATH:
                    sort_on = func.lower(Entry.path)

            statement = statement.order_by(asc(sort_on) if search.ascending else desc(sort_on))
            statement = statement.limit(page_size).offset(search.page_index * page_size)

            logger.info(
                "searching library",
                filter=search,
                query_full=str(statement.compile(compile_kwargs={"literal_binds": True})),
            )

            start_time = time.time()
            items = session.scalars(statement).fetchall()
            end_time = time.time()
            logger.info(f"SQL Execution finished ({format_timespan(end_time - start_time)})")

            res = SearchResult(
                total_count=count_all,
                items=list(items),
            )

            session.expunge_all()

            return res

    def search_tags(self, name: str | None, limit: int = 100) -> list[set[Tag]]:
        """Return a list of Tag records matching the query."""
        with Session(self.engine) as session:
            query = select(Tag).outerjoin(TagAlias).order_by(func.lower(Tag.name))
            query = query.options(
                selectinload(Tag.parent_tags),
                selectinload(Tag.aliases),
            )
            if limit > 0:
                query = query.limit(limit)

            if name:
                query = query.where(
                    or_(
                        Tag.name.icontains(name),
                        Tag.shorthand.icontains(name),
                        TagAlias.name.icontains(name),
                    )
                )

            direct_tags = set(session.scalars(query))
            ancestor_tag_ids: list[Tag] = []
            for tag in direct_tags:
                ancestor_tag_ids.extend(
                    list(session.scalars(TAG_CHILDREN_QUERY, {"tag_id": tag.id}))
                )

            ancestor_tags = session.scalars(
                select(Tag)
                .where(Tag.id.in_(ancestor_tag_ids))
                .options(selectinload(Tag.parent_tags), selectinload(Tag.aliases))
            )

            res = [
                direct_tags,
                {at for at in ancestor_tags if at not in direct_tags},
            ]

            logger.info(
                "searching tags",
                search=name,
                limit=limit,
                statement=str(query),
                results=len(res),
            )

            session.expunge_all()

            return res

    def update_entry_path(self, entry_id: int | Entry, path: Path) -> bool:
        """Set the path field of an entry.

        Returns True if the action succeeded and False if the path already exists.
        """
        if self.has_path_entry(path):
            return False
        if isinstance(entry_id, Entry):
            entry_id = entry_id.id

        with Session(self.engine) as session:
            update_stmt = (
                update(Entry)
                .where(
                    and_(
                        Entry.id == entry_id,
                    )
                )
                .values(path=path)
            )

            session.execute(update_stmt)
            session.commit()
        return True

    def remove_tag(self, tag: Tag):
        with Session(self.engine, expire_on_commit=False) as session:
            try:
                child_tags = session.scalars(
                    select(TagParent).where(TagParent.child_id == tag.id)
                ).all()
                tags_query = select(Tag).options(
                    selectinload(Tag.parent_tags), selectinload(Tag.aliases)
                )
                tag = session.scalar(tags_query.where(Tag.id == tag.id))
                aliases = session.scalars(select(TagAlias).where(TagAlias.tag_id == tag.id))

                for alias in aliases or []:
                    session.delete(alias)

                for child_tag in child_tags or []:
                    session.delete(child_tag)
                    session.expunge(child_tag)

                disam_stmt = (
                    update(Tag)
                    .where(Tag.disambiguation_id == tag.id)
                    .values(disambiguation_id=None)
                )
                session.execute(disam_stmt)
                session.flush()

                session.delete(tag)
                session.commit()
                session.expunge(tag)

                return tag

            except IntegrityError as e:
                logger.error(e)
                session.rollback()

                return None

    def update_field_position(
        self,
        field_class: type[BaseField],
        field_type: str,
        entry_ids: list[int] | int,
    ):
        if isinstance(entry_ids, int):
            entry_ids = [entry_ids]

        with Session(self.engine) as session:
            for entry_id in entry_ids:
                rows = list(
                    session.scalars(
                        select(field_class)
                        .where(
                            and_(
                                field_class.entry_id == entry_id,
                                field_class.type_key == field_type,
                            )
                        )
                        .order_by(field_class.id)
                    )
                )

                # Reassign `order` starting from 0
                for index, row in enumerate(rows):
                    row.position = index
                    session.add(row)
                    session.flush()
                if rows:
                    session.commit()

    def remove_entry_field(
        self,
        field: BaseField,
        entry_ids: list[int],
    ) -> None:
        FieldClass = type(field)  # noqa: N806

        logger.info(
            "remove_entry_field",
            field=field,
            entry_ids=entry_ids,
            field_type=field.type,
            cls=FieldClass,
            pos=field.position,
        )

        with Session(self.engine) as session:
            # remove all fields matching entry and field_type
            delete_stmt = delete(FieldClass).where(
                and_(
                    FieldClass.position == field.position,
                    FieldClass.type_key == field.type_key,
                    FieldClass.entry_id.in_(entry_ids),
                )
            )

            session.execute(delete_stmt)

            session.commit()

        # recalculate the remaining positions
        # self.update_field_position(type(field), field.type, entry_ids)

    def update_entry_field(
        self,
        entry_ids: list[int] | int,
        field: BaseField,
        content: str | datetime,
    ):
        if isinstance(entry_ids, int):
            entry_ids = [entry_ids]

        FieldClass = type(field)  # noqa: N806

        with Session(self.engine) as session:
            update_stmt = (
                update(FieldClass)
                .where(
                    and_(
                        FieldClass.position == field.position,
                        FieldClass.type == field.type,
                        FieldClass.entry_id.in_(entry_ids),
                    )
                )
                .values(value=content)
            )

            session.execute(update_stmt)
            session.commit()

    @property
    def field_types(self) -> dict[str, ValueType]:
        with Session(self.engine) as session:
            return {x.key: x for x in session.scalars(select(ValueType)).all()}

    def get_value_type(self, field_key: str) -> ValueType:
        with Session(self.engine) as session:
            field = session.scalar(select(ValueType).where(ValueType.key == field_key))
            session.expunge(field)
            return field

    def add_field_to_entry(
        self,
        entry_id: int,
        *,
        field: ValueType | None = None,
        field_id: _FieldID | str | None = None,
        value: str | datetime | None = None,
    ) -> bool:
        logger.info(
            "add_field_to_entry",
            entry_id=entry_id,
            field_type=field,
            field_id=field_id,
            value=value,
        )
        # supply only instance or ID, not both
        assert bool(field) != (field_id is not None)

        if not field:
            if isinstance(field_id, _FieldID):
                field_id = field_id.name
            field = self.get_value_type(field_id)

        field_model: TextField | DatetimeField
        if field.type in (FieldTypeEnum.TEXT_LINE, FieldTypeEnum.TEXT_BOX):
            field_model = TextField(
                type_key=field.key,
                value=value or "",
            )

        elif field.type == FieldTypeEnum.DATETIME:
            field_model = DatetimeField(
                type_key=field.key,
                value=value,
            )
        else:
            raise NotImplementedError(f"field type not implemented: {field.type}")

        with Session(self.engine) as session:
            try:
                field_model.entry_id = entry_id
                session.add(field_model)
                session.flush()
                session.commit()
            except IntegrityError as e:
                logger.error(e)
                session.rollback()
                return False
                # TODO - trigger error signal

        # recalculate the positions of fields
        self.update_field_position(
            field_class=type(field_model),
            field_type=field.key,
            entry_ids=entry_id,
        )
        return True

    def tag_from_strings(self, strings: list[str] | str) -> list[int]:
        """Create a Tag from a given string."""
        # TODO: Port over tag searching with aliases fallbacks
        # and context clue ranking for string searches.
        tags: list[int] = []

        if isinstance(strings, str):
            strings = [strings]

        with Session(self.engine) as session:
            for string in strings:
                tag = session.scalar(select(Tag).where(Tag.name == string))
                if tag:
                    tags.append(tag.id)
                else:
                    new = session.add(Tag(name=string))  # type: ignore
                    if new:
                        tags.append(new.id)
                        session.flush()
            session.commit()
        return tags

    def add_namespace(self, namespace: Namespace) -> bool:
        """Add a namespace value to the library.

        Args:
            namespace(str): The namespace slug. No special characters
        """
        with Session(self.engine) as session:
            if not namespace.namespace:
                logger.warning("[LIBRARY][add_namespace] Namespace slug must not be empty")
                return False

            slug = namespace.namespace
            try:
                slug = slugify(namespace.namespace)
            except ReservedNamespaceError:
                logger.error(
                    f"[LIBRARY][add_namespace] Will not add a namespace with the reserved prefix:"
                    f"{RESERVED_NAMESPACE_PREFIX}",
                    namespace=namespace,
                )

            namespace_obj = Namespace(
                namespace=slug,
                name=namespace.name,
            )

            try:
                session.add(namespace_obj)
                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                logger.error("IntegrityError")
                return False

    def delete_namespace(self, namespace: Namespace | str):
        """Delete a namespace and any connected data from the library."""
        if isinstance(namespace, str):
            if namespace.startswith(RESERVED_NAMESPACE_PREFIX):
                raise ReservedNamespaceError
        else:
            if namespace.namespace.startswith(RESERVED_NAMESPACE_PREFIX):
                raise ReservedNamespaceError

        with Session(self.engine, expire_on_commit=False) as session:
            try:
                namespace_: Namespace | None = None
                if isinstance(namespace, str):
                    namespace_ = session.scalar(
                        select(Namespace).where(Namespace.namespace == namespace)
                    )
                else:
                    namespace_ = namespace

                if not namespace_:
                    raise Exception
                session.delete(namespace_)
                session.flush()

                colors = session.scalars(
                    select(TagColorGroup).where(TagColorGroup.namespace == namespace_.namespace)
                )
                for color in colors:
                    session.delete(color)
                    session.flush()

                session.commit()

            except IntegrityError as e:
                logger.error(e)
                session.rollback()
                return None

    def add_tag(
        self,
        tag: Tag,
        parent_ids: list[int] | set[int] | None = None,
        alias_names: list[str] | set[str] | None = None,
        alias_ids: list[int] | set[int] | None = None,
    ) -> Tag | None:
        with Session(self.engine, expire_on_commit=False) as session:
            try:
                session.add(tag)
                session.flush()

                if parent_ids is not None:
                    self.update_parent_tags(tag, parent_ids, session)

                if alias_ids is not None and alias_names is not None:
                    self.update_aliases(tag, alias_ids, alias_names, session)

                session.commit()
                session.expunge(tag)
                return tag

            except IntegrityError as e:
                logger.error(e)
                session.rollback()
                return None

    def add_tags_to_entries(
        self, entry_ids: int | list[int], tag_ids: int | list[int] | set[int]
    ) -> bool:
        """Add one or more tags to one or more entries."""
        entry_ids_ = [entry_ids] if isinstance(entry_ids, int) else entry_ids
        tag_ids_ = [tag_ids] if isinstance(tag_ids, int) else tag_ids
        with Session(self.engine, expire_on_commit=False) as session:
            for tag_id in tag_ids_:
                for entry_id in entry_ids_:
                    try:
                        session.add(TagEntry(tag_id=tag_id, entry_id=entry_id))
                        session.flush()
                    except IntegrityError:
                        session.rollback()
            try:
                session.commit()
            except IntegrityError as e:
                logger.warning("[Library][add_tags_to_entries]", warning=e)
                session.rollback()
                return False
            return True

    def remove_tags_from_entries(
        self, entry_ids: int | list[int], tag_ids: int | list[int] | set[int]
    ) -> bool:
        """Remove one or more tags from one or more entries."""
        entry_ids_ = [entry_ids] if isinstance(entry_ids, int) else entry_ids
        tag_ids_ = [tag_ids] if isinstance(tag_ids, int) else tag_ids
        with Session(self.engine, expire_on_commit=False) as session:
            try:
                for tag_id in tag_ids_:
                    for entry_id in entry_ids_:
                        tag_entry = session.scalars(
                            select(TagEntry).where(
                                and_(
                                    TagEntry.tag_id == tag_id,
                                    TagEntry.entry_id == entry_id,
                                )
                            )
                        ).first()
                        if tag_entry:
                            session.delete(tag_entry)
                            session.flush()
                session.commit()
                return True
            except IntegrityError as e:
                logger.error(e)
                session.rollback()
                return False

    def add_color(self, color_group: TagColorGroup) -> TagColorGroup | None:
        with Session(self.engine, expire_on_commit=False) as session:
            try:
                session.add(color_group)
                session.commit()
                session.expunge(color_group)
                return color_group

            except IntegrityError as e:
                logger.error(
                    "[Library] Could not add color, trying to update existing value instead.",
                    error=e,
                )
                session.rollback()
                return None

    def delete_color(self, color: TagColorGroup):
        with Session(self.engine, expire_on_commit=False) as session:
            try:
                session.delete(color)
                session.commit()

            except IntegrityError as e:
                logger.error(e)
                session.rollback()
                return None

    def save_library_backup_to_disk(self) -> Path:
        assert isinstance(self.library_dir, Path)
        makedirs(str(self.library_dir / TS_FOLDER_NAME / BACKUP_FOLDER_NAME), exist_ok=True)

        filename = f"ts_library_backup_{datetime.now(UTC).strftime('%Y_%m_%d_%H%M%S')}.sqlite"

        target_path = self.library_dir / TS_FOLDER_NAME / BACKUP_FOLDER_NAME / filename

        shutil.copy2(
            self.library_dir / TS_FOLDER_NAME / self.SQL_FILENAME,
            target_path,
        )

        logger.info("Library backup saved to disk.", path=target_path)

        return target_path

    def get_tag(self, tag_id: int) -> Tag | None:
        with Session(self.engine) as session:
            tags_query = select(Tag).options(
                selectinload(Tag.parent_tags),
                selectinload(Tag.aliases),
                joinedload(Tag.color),
            )
            tag = session.scalar(tags_query.where(Tag.id == tag_id))

            session.expunge(tag)
            for parent in tag.parent_tags:
                session.expunge(parent)

            for alias in tag.aliases:
                session.expunge(alias)

        return tag

    def get_tag_by_name(self, tag_name: str) -> Tag | None:
        with Session(self.engine) as session:
            statement = (
                select(Tag)
                .outerjoin(TagAlias)
                .where(or_(Tag.name == tag_name, TagAlias.name == tag_name))
            )
            return session.scalar(statement)

    def get_alias(self, tag_id: int, alias_id: int) -> TagAlias | None:
        with Session(self.engine) as session:
            alias_query = select(TagAlias).where(TagAlias.id == alias_id, TagAlias.tag_id == tag_id)

            return session.scalar(alias_query.where(TagAlias.id == alias_id))

    def get_tag_color(self, slug: str, namespace: str) -> TagColorGroup | None:
        with Session(self.engine) as session:
            statement = select(TagColorGroup).where(
                and_(TagColorGroup.slug == slug, TagColorGroup.namespace == namespace)
            )

            return session.scalar(statement)

    def add_parent_tag(self, parent_id: int, child_id: int) -> bool:
        if parent_id == child_id:
            return False

        # open session and save as parent tag
        with Session(self.engine) as session:
            parent_tag = TagParent(
                parent_id=parent_id,
                child_id=child_id,
            )

            try:
                session.add(parent_tag)
                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                logger.error("IntegrityError")
                return False

    def add_alias(self, name: str, tag_id: int) -> bool:
        with Session(self.engine) as session:
            if not name:
                logger.warning("[LIBRARY][add_alias] Alias value must not be empty")
                return False
            alias = TagAlias(
                name=name,
                tag_id=tag_id,
            )

            try:
                session.add(alias)
                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                logger.error("IntegrityError")
                return False

    def remove_parent_tag(self, base_id: int, remove_tag_id: int) -> bool:
        with Session(self.engine) as session:
            p_id = base_id
            r_id = remove_tag_id
            remove = session.query(TagParent).filter_by(parent_id=p_id, child_id=r_id).one()
            session.delete(remove)
            session.commit()

        return True

    def update_tag(
        self,
        tag: Tag,
        parent_ids: list[int] | set[int] | None = None,
        alias_names: list[str] | set[str] | None = None,
        alias_ids: list[int] | set[int] | None = None,
    ) -> None:
        """Edit a Tag in the Library."""
        self.add_tag(tag, parent_ids, alias_names, alias_ids)

    def update_color(self, old_color_group: TagColorGroup, new_color_group: TagColorGroup) -> None:
        """Update a TagColorGroup in the Library. If it doesn't already exist, create it."""
        with Session(self.engine) as session:
            existing_color = session.scalar(
                select(TagColorGroup).where(
                    and_(
                        TagColorGroup.namespace == old_color_group.namespace,
                        TagColorGroup.slug == old_color_group.slug,
                    )
                )
            )
            if existing_color:
                update_color_stmt = (
                    update(TagColorGroup)
                    .where(
                        and_(
                            TagColorGroup.namespace == old_color_group.namespace,
                            TagColorGroup.slug == old_color_group.slug,
                        )
                    )
                    .values(
                        slug=new_color_group.slug,
                        namespace=new_color_group.namespace,
                        name=new_color_group.name,
                        primary=new_color_group.primary,
                        secondary=new_color_group.secondary,
                        color_border=new_color_group.color_border,
                    )
                )
                session.execute(update_color_stmt)
                session.flush()
                update_tags_stmt = (
                    update(Tag)
                    .where(
                        and_(
                            Tag.color_namespace == old_color_group.namespace,
                            Tag.color_slug == old_color_group.slug,
                        )
                    )
                    .values(
                        color_namespace=new_color_group.namespace,
                        color_slug=new_color_group.slug,
                    )
                )
                session.execute(update_tags_stmt)
                session.commit()
            else:
                self.add_color(new_color_group)

    def update_aliases(self, tag, alias_ids, alias_names, session):
        prev_aliases = session.scalars(select(TagAlias).where(TagAlias.tag_id == tag.id)).all()

        for alias in prev_aliases:
            if alias.id not in alias_ids or alias.name not in alias_names:
                session.delete(alias)
            else:
                alias_ids.remove(alias.id)
                alias_names.remove(alias.name)

        for alias_name in alias_names:
            alias = TagAlias(alias_name, tag.id)
            session.add(alias)

    def update_parent_tags(self, tag: Tag, parent_ids: list[int] | set[int], session):
        if tag.id in parent_ids:
            parent_ids.remove(tag.id)

        if tag.disambiguation_id not in parent_ids:
            tag.disambiguation_id = None

        # load all tag's parent tags to know which to remove
        prev_parent_tags = session.scalars(
            select(TagParent).where(TagParent.parent_id == tag.id)
        ).all()

        for parent_tag in prev_parent_tags:
            if parent_tag.child_id not in parent_ids:
                session.delete(parent_tag)
            else:
                # no change, remove from list
                parent_ids.remove(parent_tag.child_id)

                # create remaining items
        for parent_id in parent_ids:
            # add new parent tag
            parent_tag = TagParent(
                parent_id=tag.id,
                child_id=parent_id,
            )
            session.add(parent_tag)

    def prefs(self, key: LibraryPrefs):
        # load given item from Preferences table
        with Session(self.engine) as session:
            return session.scalar(select(Preferences).where(Preferences.key == key.name)).value

    def set_prefs(self, key: LibraryPrefs, value) -> None:
        # set given item in Preferences table
        with Session(self.engine) as session:
            # load existing preference and update value
            pref = session.scalar(select(Preferences).where(Preferences.key == key.name))
            pref.value = value
            session.add(pref)
            session.commit()
            # TODO - try/except

    def mirror_entry_fields(self, *entries: Entry) -> None:
        """Mirror fields among multiple Entry items."""
        fields = {}
        # load all fields
        existing_fields = {field.type_key for field in entries[0].fields}
        for entry in entries:
            for entry_field in entry.fields:
                fields[entry_field.type_key] = entry_field

        # assign the field to all entries
        for entry in entries:
            for field_key, field in fields.items():
                if field_key not in existing_fields:
                    self.add_field_to_entry(
                        entry_id=entry.id,
                        field_id=field.type_key,
                        value=field.value,
                    )

    def merge_entries(self, from_entry: Entry, into_entry: Entry) -> None:
        """Add fields and tags from the first entry to the second, and then delete the first."""
        for field in from_entry.fields:
            self.add_field_to_entry(
                entry_id=into_entry.id,
                field_id=field.type_key,
                value=field.value,
            )
        tag_ids = [tag.id for tag in from_entry.tags]
        self.add_tags_to_entries(into_entry.id, tag_ids)
        self.remove_entries([from_entry.id])

    @property
    def tag_color_groups(self) -> dict[str, list[TagColorGroup]]:
        """Return every TagColorGroup in the library."""
        with Session(self.engine) as session:
            color_groups: dict[str, list[TagColorGroup]] = {}
            results = session.scalars(select(TagColorGroup).order_by(asc(TagColorGroup.namespace)))
            for color in results:
                if not color_groups.get(color.namespace):
                    color_groups[color.namespace] = []
                color_groups[color.namespace].append(color)
                session.expunge(color)

            # Add empty namespaces that are available for use.
            empty_namespaces = session.scalars(
                select(Namespace)
                .where(Namespace.namespace.not_in(color_groups.keys()))
                .order_by(asc(Namespace.namespace))
            )
            for en in empty_namespaces:
                if not color_groups.get(en.namespace):
                    color_groups[en.namespace] = []
                session.expunge(en)

        return dict(
            sorted(color_groups.items(), key=lambda kv: self.get_namespace_name(kv[0]).lower())
        )

    @property
    def namespaces(self) -> list[Namespace]:
        """Return every Namespace in the library."""
        with Session(self.engine) as session:
            namespaces = session.scalars(select(Namespace).order_by(asc(Namespace.name)))
            return list(namespaces)

    def get_namespace_name(self, namespace: str) -> str:
        with Session(self.engine) as session:
            result = session.scalar(select(Namespace).where(Namespace.namespace == namespace))
            if result:
                session.expunge(result)

        return "" if not result else result.name
