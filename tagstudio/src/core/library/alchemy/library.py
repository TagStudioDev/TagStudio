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
from uuid import uuid4
from warnings import catch_warnings

import structlog
from humanfriendly import format_timespan
from sqlalchemy import (
    URL,
    ColumnExpressionArgument,
    Engine,
    NullPool,
    and_,
    asc,
    create_engine,
    delete,
    desc,
    exists,
    func,
    or_,
    select,
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
from src.core.library.json.library import Library as JsonLibrary  # type: ignore

from ...constants import (
    BACKUP_FOLDER_NAME,
    LEGACY_TAG_FIELD_IDS,
    RESERVED_TAG_END,
    RESERVED_TAG_START,
    TAG_ARCHIVED,
    TAG_FAVORITE,
    TAG_META,
    TS_FOLDER_NAME,
)
from ...enums import LibraryPrefs
from . import default_color_groups
from .db import make_tables
from .enums import MAX_SQL_VARIABLES, FieldTypeEnum, FilterState, SortingModeEnum
from .fields import (
    BaseField,
    DatetimeField,
    TextField,
    _FieldID,
)
from .joins import TagEntry, TagParent
from .models import Entry, Folder, Namespace, Preferences, Tag, TagAlias, TagColorGroup, ValueType
from .visitors import SQLBoolExpressionBuilder

logger = structlog.get_logger(__name__)


def slugify(input_string: str) -> str:
    # Convert to lowercase and normalize unicode characters
    slug = unicodedata.normalize("NFKD", input_string.lower())

    # Remove non-word characters (except hyphens and spaces)
    slug = re.sub(r"[^\w\s-]", "", slug).strip()

    # Replace spaces with hyphens
    slug = re.sub(r"[-\s]+", "-", slug)

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
    json_migration_req: bool = False


class Library:
    """Class for the Library object, and all CRUD operations made upon it."""

    library_dir: Path | None = None
    storage_path: Path | str | None
    engine: Engine | None
    folder: Folder | None
    included_files: set[Path] = set()

    SQL_FILENAME: str = "ts_library.sqlite"
    JSON_FILENAME: str = "ts_library.json"

    def close(self):
        if self.engine:
            self.engine.dispose()
        self.library_dir = None
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
            self.add_tag(
                Tag(
                    id=tag.id,
                    name=tag.name,
                    shorthand=tag.shorthand,
                    color_namespace=color_namespace,
                    color_slug=color_slug,
                )
            )
            # Apply user edits to built-in JSON tags.
            if tag.id in range(RESERVED_TAG_START, RESERVED_TAG_END + 1):
                updated_tag = self.get_tag(tag.id)
                if not updated_tag:
                    continue
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
                )
                for entry in json_lib.entries
            ]
        )
        for entry in json_lib.entries:
            for field in entry.fields:
                for k, v in field.items():
                    # Old tag fields get added as tags
                    if k in LEGACY_TAG_FIELD_IDS:
                        self.add_tags_to_entry(entry_id=entry.id + 1, tag_ids=v)
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
        logger.info(f"Library Converted! ({format_timespan(end_time-start_time)})")

    def get_field_name_from_id(self, field_id: int) -> _FieldID:
        for f in _FieldID:
            if field_id == f.value.id:
                return f
        return None

    def open_library(self, library_dir: Path, storage_path: str | None = None) -> LibraryStatus:
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

        logger.info(
            "Opening SQLite Library", library_dir=library_dir, connection_string=connection_string
        )
        self.engine = create_engine(connection_string, poolclass=poolclass)
        with Session(self.engine) as session:
            make_tables(self.engine)

            # TODO: Determine a good way of updating built-in data after updates.

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

            # dont check db version when creating new library
            if not is_new:
                db_version = session.scalar(
                    select(Preferences).where(Preferences.key == LibraryPrefs.DB_VERSION.name)
                )

                if not db_version:
                    return LibraryStatus(
                        success=False,
                        message=(
                            "Library version mismatch.\n"
                            f"Found: v0, expected: v{LibraryPrefs.DB_VERSION.default}"
                        ),
                    )

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

            db_version = session.scalar(
                select(Preferences).where(Preferences.key == LibraryPrefs.DB_VERSION.name)
            )
            # if the db version is different, we cant proceed
            if db_version.value != LibraryPrefs.DB_VERSION.default:
                logger.error(
                    "DB version mismatch",
                    db_version=db_version.value,
                    expected=LibraryPrefs.DB_VERSION.default,
                )
                return LibraryStatus(
                    success=False,
                    message=(
                        "Library version mismatch.\n"
                        f"Found: v{db_version.value}, expected: v{LibraryPrefs.DB_VERSION.default}"
                    ),
                )

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

        # everything is fine, set the library path
        self.library_dir = library_dir
        return LibraryStatus(success=True, library_path=library_dir)

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
        with Session(self.engine) as session:
            statement = select(Entry).where(Entry.id == entry_id)
            if with_fields:
                statement = (
                    statement.outerjoin(Entry.text_fields)
                    .outerjoin(Entry.datetime_fields)
                    .options(selectinload(Entry.text_fields), selectinload(Entry.datetime_fields))
                )
            if with_tags:
                statement = (
                    statement.outerjoin(Entry.tags)
                    .outerjoin(TagAlias)
                    .options(
                        selectinload(Entry.tags).options(
                            joinedload(Tag.aliases),
                            joinedload(Tag.parent_tags),
                        )
                    )
                )
            entry = session.scalar(statement)
            if not entry:
                return None
            session.expunge(entry)
            make_transient(entry)
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

            entries = session.execute(statement).scalars()
            entries = entries.unique()

            for entry in entries:
                yield entry
                session.expunge(entry)

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
                logger.exception("IntegrityError")
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

    def get_paths(self, glob: str | None = None) -> list[str]:
        with Session(self.engine) as session:
            paths = session.scalars(select(Entry.path)).unique()

        path_strings: list[str] = list(map(lambda x: x.as_posix(), paths))
        return path_strings

    def search_library(
        self,
        search: FilterState,
    ) -> SearchResult:
        """Filter library by search query.

        :return: number of entries matching the query and one page of results.
        """
        assert isinstance(search, FilterState)
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
            count_all: int = session.execute(query_count).scalar()
            end_time = time.time()
            logger.info(f"finished counting ({format_timespan(end_time-start_time)})")

            sort_on: ColumnExpressionArgument = Entry.id
            match search.sorting_mode:
                case SortingModeEnum.DATE_ADDED:
                    sort_on = Entry.id

            statement = statement.order_by(asc(sort_on) if search.ascending else desc(sort_on))
            statement = statement.limit(search.limit).offset(search.offset)

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

    def search_tags(
        self,
        name: str | None,
    ) -> list[Tag]:
        """Return a list of Tag records matching the query."""
        tag_limit = 100

        with Session(self.engine) as session:
            query = select(Tag)
            query = query.options(
                selectinload(Tag.parent_tags),
                selectinload(Tag.aliases),
            ).limit(tag_limit)

            if name:
                query = query.where(
                    or_(
                        Tag.name.icontains(name),
                        Tag.shorthand.icontains(name),
                    )
                )

            tags = session.scalars(query)

            res = list(tags)

            logger.info(
                "searching tags",
                search=name,
                statement=str(query),
                results=len(res),
            )

            session.expunge_all()

            return res

    def update_entry_path(self, entry_id: int | Entry, path: Path) -> None:
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

                session.delete(tag)
                session.commit()
                session.expunge(tag)

                return tag

            except IntegrityError as e:
                logger.exception(e)
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
                logger.exception(e)
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
                    new = session.add(Tag(name=string))
                    if new:
                        tags.append(new.id)
                        session.flush()
            session.commit()
        return tags

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
                logger.exception(e)
                session.rollback()
                return None

    def add_tags_to_entry(self, entry_id: int, tag_ids: int | list[int] | set[int]) -> bool:
        """Add one or more tags to an entry."""
        tag_ids_ = [tag_ids] if isinstance(tag_ids, int) else tag_ids
        with Session(self.engine, expire_on_commit=False) as session:
            try:
                # TODO: Optimize this by using a single query to update.
                for tag_id in tag_ids_:
                    session.add(TagEntry(tag_id=tag_id, entry_id=entry_id))
                    session.flush()
                session.commit()
                return True
            except IntegrityError as e:
                logger.warning("[add_tags_to_entry]", warning=e)
                session.rollback()
                return False

    def remove_tags_from_entry(self, entry_id: int, tag_ids: int | list[int] | set[int]) -> bool:
        """Remove one or more tags from an entry."""
        tag_ids_ = [tag_ids] if isinstance(tag_ids, int) else tag_ids
        with Session(self.engine, expire_on_commit=False) as session:
            try:
                for tag_id in tag_ids_:
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
                        session.commit()
                session.commit()
                return True
            except IntegrityError as e:
                logger.exception(e)
                session.rollback()
                return False

    def save_library_backup_to_disk(self) -> Path:
        assert isinstance(self.library_dir, Path)
        makedirs(str(self.library_dir / TS_FOLDER_NAME / BACKUP_FOLDER_NAME), exist_ok=True)

        filename = f'ts_library_backup_{datetime.now(UTC).strftime("%Y_%m_%d_%H%M%S")}.sqlite'

        target_path = self.library_dir / TS_FOLDER_NAME / BACKUP_FOLDER_NAME / filename

        shutil.copy2(
            self.library_dir / TS_FOLDER_NAME / self.SQL_FILENAME,
            target_path,
        )

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
                logger.exception("IntegrityError")
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
                logger.exception("IntegrityError")
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

    def update_parent_tags(self, tag, parent_ids, session):
        if tag.id in parent_ids:
            parent_ids.remove(tag.id)

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
        return color_groups

    def get_namespace_name(self, namespace: str) -> str:
        with Session(self.engine) as session:
            result = session.scalar(select(Namespace).where(Namespace.namespace == namespace))
            if result:
                session.expunge(result)

        return "" if not result else result.name
