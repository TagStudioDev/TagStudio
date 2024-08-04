import datetime
import time
from pathlib import Path
from typing import Iterator, Literal, Any

import structlog
from sqlalchemy import and_, or_, select, create_engine, Engine, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    Session,
    contains_eager,
    selectinload,
    make_transient,
)

from .db import make_tables
from .enums import TagColor, FilterState
from .fields import (
    DEFAULT_FIELDS,
    DatetimeField,
    Field,
    TagBoxField,
    TagBoxTypes,
    TextField,
)
from .joins import TagField
from .models import Entry, Tag, TagAlias
from ...constants import TS_FOLDER_NAME

LIBRARY_FILENAME: str = "ts_library.sqlite"

logger = structlog.get_logger(__name__)


def get_library_defaults() -> list[Tag]:
    archive_tag = Tag(
        name="Archived",
        aliases={TagAlias(name="Archive")},
        color=TagColor.red,
    )

    favorite_tag = Tag(
        name="Favorite",
        aliases={
            TagAlias(name="Favorited"),
            TagAlias(name="Favorites"),
        },
        color=TagColor.yellow,
    )

    return [archive_tag, favorite_tag]


class Library:
    """Class for the Library object, and all CRUD operations made upon it."""

    library_dir: Path | str | None
    missing_files: list[str]
    dupe_files: list[str]
    engine: Engine | None
    dupe_entries: list[Entry]  # TODO
    ext_list: list[str]  # TODO
    is_exclude_list: bool  # TODO

    def __init__(self):
        self.clear_internal_vars()

    def open_library(self, library_dir: Path | str) -> None:
        self.clear_internal_vars()

        if library_dir == ":memory:":
            connection_string = f"sqlite:///{library_dir}"
            self.library_dir = library_dir
        else:
            self.library_dir = Path(library_dir)
            self.verify_ts_folders(self.library_dir)

            connection_string = (
                f"sqlite:///{self.library_dir / TS_FOLDER_NAME / LIBRARY_FILENAME}"
            )

        logger.info("opening library", connection_string=connection_string)
        self.engine = create_engine(connection_string)
        session = Session(self.engine)
        with session.begin():
            make_tables(self.engine)

    def delete_item(self, item):
        logger.info("deleting item", item=item)
        with Session(self.engine) as session, session.begin():
            session.delete(item)
            session.commit()

    def remove_field_tag(self, field: TagBoxField, tag_id: int):
        with Session(self.engine) as session, session.begin():
            tag = session.scalar(select(Tag).where(Tag.id == tag_id))

            # remove instance of TagField matching combination of `field` and `tag_id`
            session.delete(
                session.scalar(
                    select(TagField).where(
                        and_(
                            TagField.field_id == field.id,
                            TagField.tag_id == tag_id,
                        )
                    )
                )
            )

            session.commit()

    def get_entry(self, entry_id: int) -> Entry | None:
        """Load entry without joins."""
        with Session(self.engine) as session, session.begin():
            entry = session.scalar(select(Entry).where(Entry.id == entry_id))
            if not entry:
                return None
            session.expunge(entry)
            make_transient(entry)
            return entry

    @property
    def entries(self) -> list[Entry]:
        """Load all entries with joins.
        Debugging purposes only.
        """
        with Session(self.engine) as session, session.begin():
            stmt = (
                select(Entry)
                .outerjoin(Entry.text_fields)
                .outerjoin(Entry.datetime_fields)
                .outerjoin(Entry.tag_box_fields)
                .options(
                    contains_eager(Entry.text_fields),
                    contains_eager(Entry.datetime_fields),
                    contains_eager(Entry.tag_box_fields).selectinload(TagBoxField.tags),
                )
                .distinct()
            )

            entries = session.execute(stmt).scalars().unique().all()

            session.expunge_all()

            return list(entries)

    @property
    def tags(self) -> list[Tag]:
        with Session(self.engine) as session, session.begin():
            tags = list(session.scalars(select(Tag)).all())
            session.expunge_all()

        return list(tags)

    def save_library_to_disk(self):
        logger.error("save_library_to_disk to be implemented")

    def verify_ts_folders(self, library_dir: Path) -> None:
        """Verify/create folders required by TagStudio."""
        if library_dir is None:
            raise ValueError("No path set.")

        if not library_dir.exists():
            raise ValueError("Invalid library directory.")

        full_ts_path = library_dir / TS_FOLDER_NAME
        if not full_ts_path.exists():
            logger.info("creating library directory", dir=full_ts_path)
            full_ts_path.mkdir(parents=True, exist_ok=True)

    def verify_default_tags(self, tag_list: list) -> list:
        """
        Ensures that the default builtin tags  are present in the Library's
        save file. Takes in and returns the tag dictionary from the JSON file.
        """
        missing: list = []

        for m in missing:
            tag_list.append(m)

        return tag_list

    def clear_internal_vars(self):
        """Clears the internal variables of the Library object."""
        self.library_dir = None
        self.missing_files = []
        self.dupe_files = []
        self.ignored_extensions = []
        self.missing_matches = {}

    def refresh_dir(self) -> Iterator[int]:
        """Scan a directory for files, and add those relative filenames to internal variables."""
        if self.library_dir is None:
            raise ValueError("No library path set.")

        # Scans the directory for files, keeping track of:
        #   - Total file count
        start_time = time.time()
        self.files_not_in_library: list[Path] = []
        self.dir_file_count = 0

        for path in self.library_dir.glob("**/*"):
            str_path = str(path)
            if any(
                [
                    path.is_dir()
                    or "$RECYCLE.BIN" in str_path
                    or TS_FOLDER_NAME in str_path
                    or "tagstudio_thumbs" in str_path
                ]
            ):
                continue

            suffix = path.suffix.lower().lstrip(".")
            if suffix in self.ignored_extensions:
                continue

            self.dir_file_count += 1
            relative_path = path.relative_to(self.library_dir)
            # TODO - load these in batch somehow
            if not self.has_item(path=relative_path):
                logger.info("item not in library yet", path=relative_path)
                self.files_not_in_library.append(relative_path)

            end_time = time.time()
            # Yield output every 1/30 of a second
            if (end_time - start_time) > 0.034:
                yield self.dir_file_count

    def has_item(self, path: Path) -> bool:
        """Check if item with given path is in library already."""
        with Session(self.engine) as session, session.begin():
            # check if item with given path is in the database
            query = select(Entry).where(Entry.path == path)
            res = session.scalar(query)
            logger.debug(
                "check item presence",
                # query=str(query),
                path=path,
                present=bool(res),
            )
            return bool(res)

    def add_entries(self, items: list[Entry]) -> list[int]:
        """Add multiple Entry records to the Library."""
        if not items:
            return []

        with Session(self.engine) as session, session.begin():
            # add all items
            session.add_all(items)
            session.flush()

            new_ids = [item.id for item in items]

            session.expunge_all()

            session.commit()

        return new_ids

    def refresh_missing_files(self) -> Iterator[int]:
        """Track the number of Entries that point to an invalid file path."""
        self.missing_files.clear()

        if self.library_dir is None:
            raise ValueError("No library path set.")

        for i, entry in enumerate(self.entries):
            full_path = self.library_dir / entry.path
            if not full_path.exists() or not full_path.is_file():
                self.missing_files.append(str(full_path))
            yield i

    def remove_entry(self, entry_id: int) -> None:
        """Remove an Entry from the Library."""
        with Session(self.engine) as session, session.begin():
            entry = session.scalar(select(Entry).where(Entry.id == entry_id))
            if entry is None:
                raise ValueError("")
            session.delete(entry)

    def add_new_files_as_entries(self) -> list[int]:
        """Add files from the `files_not_in_library` list to the Library as Entries. Returns list of added indices."""
        entries = []
        for path in self.files_not_in_library:
            entries.append(
                Entry(
                    path=path,
                )
            )

        return self.add_entries(entries)

    def search_library(
        self,
        search: FilterState,
    ) -> tuple[int, list[Entry]]:
        """Filter library by search query.

        :return: number of entries matching the query and one page of results.
        """
        assert isinstance(search, FilterState)
        assert self.engine
        with Session(self.engine, expire_on_commit=False) as session, session.begin():
            statement = (
                select(Entry)
                .outerjoin(Entry.text_fields)
                .outerjoin(Entry.datetime_fields)
                .outerjoin(Entry.tag_box_fields)
                .outerjoin(TagBoxField.tags)
                .options(
                    contains_eager(Entry.text_fields),
                    contains_eager(Entry.datetime_fields),
                    contains_eager(Entry.tag_box_fields)
                    .contains_eager(TagBoxField.tags)
                    .options(selectinload(Tag.aliases), selectinload(Tag.subtags)),
                )
            )

            query_count = select(func.count()).select_from(statement.alias("entries"))
            count_all: int = session.execute(query_count).scalar()

            # ADD limit and offset
            statement = statement.limit(search.limit).offset(search.offset)

            lookup_strategy = None

            if search.name:
                lookup_strategy = "tag_name"
                statement = statement.where(
                    or_(
                        Tag.name == search.name,
                        Tag.shorthand == search.name,
                    )
                ).distinct()

            elif search.id:
                lookup_strategy = "id"
                statement = statement.where(Entry.id == search.id)
            elif search.tag_id:
                lookup_strategy = "tag_id"
                statement = statement.where(Tag.id == search.tag_id)

            # TODO - add other lookups

            logger.info(
                "searching library",
                filter=search,
                lookup_strategy=lookup_strategy,
                query_full=statement.compile(compile_kwargs={"literal_binds": True}),
            )

            entries_ = list(session.scalars(statement).unique())

            [make_transient(x) for x in entries_]  # type: ignore
            session.expunge_all()

            return count_all, list(entries_)

    def search_tags(
        self,
        search: FilterState,
    ) -> list[Tag]:
        """Return a list of Tag records matching the query."""

        with Session(self.engine) as session, session.begin():
            query = select(Tag)
            query = query.options(
                selectinload(Tag.subtags),
                selectinload(Tag.aliases),
            )

            if search.name:
                query = query.where(
                    or_(
                        Tag.name == search.name,
                        Tag.shorthand == search.name,
                        # Tag.id == search.query,
                    )
                )

            tags = session.scalars(query)

            res = list(tags)

            logger.info(
                "searching tags",
                search=search,
                statement=str(query),
                results=len(res),
            )

            session.expunge_all()
            return res

    def get_all_child_tag_ids(self, tag_id: int) -> list[int]:
        """Recursively traverse a Tag's subtags and return a list of all children tags."""

        all_subtags: set[int] = {tag_id}

        with Session(self.engine) as session, session.begin():
            tag = session.scalar(select(Tag).where(Tag.id == tag_id))
            if tag is None:
                raise ValueError(f"No tag found with id {tag_id}.")

            subtag_ids = tag.subtag_ids

        all_subtags.update(subtag_ids)

        for sub_id in subtag_ids:
            all_subtags.update(self.get_all_child_tag_ids(sub_id))

        return list(all_subtags)

    def update_entry_path(self, entry: int | Entry, path: str) -> None:
        if isinstance(entry, Entry):
            entry = entry.id

        with Session(self.engine) as session, session.begin():
            entry_object = session.scalars(select(Entry).where(Entry.id == entry)).one()

            entry_object.path = Path(path)

    def add_generic_data_to_entry(self):
        raise NotImplementedError

    def remove_tag_from_field(self, tag: Tag, field: TagBoxField) -> None:
        with Session(self.engine) as session, session.begin():
            field_ = session.scalars(
                select(TagBoxField).where(TagBoxField.id == field.id)
            ).one()

            tag = session.scalars(select(Tag).where(Tag.id == tag.id)).one()

            field_.tags.remove(tag)

    def remove_field(
        self,
        field: Field,
        entry_ids: list[int],
    ) -> None:
        with Session(self.engine) as session, session.begin():
            fields = session.scalars(
                select(field.__class__).where(
                    and_(
                        field.__class__.name == field.name,
                        field.__class__.entry_id.in_(entry_ids),
                    )
                )
            )

            for field_ in fields:
                session.delete(field_)

    def update_field(
        self,
        field: Field,
        content: str | datetime.datetime | set[Tag],
        entry_ids: list[int],
        mode: Literal["replace", "append", "remove"],
    ):
        with Session(self.engine) as session, session.begin():
            fields = session.scalars(
                select(field.__class__).where(
                    and_(
                        field.__class__.name == field.name,
                        field.__class__.entry_id.in_(entry_ids),
                    )
                )
            )
            for field_ in fields:
                if mode == "replace":
                    # TODO
                    field_.value = content  # type: ignore
                else:
                    raise NotImplementedError

    def add_field_to_entry(self, entry: Entry, field_id: int) -> None:
        logger.info("adding field to entry", entry=entry, field_id=field_id)
        # TODO - using entry here directly doesnt work, as it's expunged from session
        # so the session tries to insert it again which fails

        default_field = DEFAULT_FIELDS[field_id]

        logger.info("found field type", field_type=default_field.class_)

        field: Any
        with Session(self.engine) as session, session.begin():
            if default_field.class_ == TextField:
                field = TextField(
                    name=default_field.name,
                    type=default_field.type,
                    value="",
                    entry_id=entry.id,
                )
                # entry.text_fields.append(field)
            elif default_field.class_ == TagBoxField:
                field = TagBoxField(
                    name=default_field.name,
                    type=default_field.type,
                    entry_id=entry.id,
                )
                # entry.tag_box_fields.append(field)
            elif default_field.class_ == DatetimeField:
                field = DatetimeField(
                    name=default_field.name,
                    type=default_field.type,
                    entry_id=entry.id,
                )
                # entry.datetime_fields.append(field)
            else:
                raise ValueError("Unknown field.")

            session.add(field)
            session.commit()

    def add_tag(self, tag: Tag) -> bool:
        with Session(self.engine, expire_on_commit=False) as session, session.begin():
            try:
                session.add(tag)
                session.commit()
            except IntegrityError as e:
                logger.exception(e)
                session.rollback()
                return False
            else:
                return True

    def add_tag_to_field(
        self,
        tag: int | Tag,
        field: TagBoxField,
    ) -> None:
        if isinstance(tag, Tag):
            tag = tag.id

        with Session(self.engine) as session, session.begin():
            tag_object = session.scalars(select(Tag).where(Tag.id == tag)).one()

            field_ = session.scalars(
                select(TagBoxField).where(TagBoxField.id == field.id)
            ).one()

            field_.tags.add(tag_object)

    def add_tag_to_entry_meta_tags(self, tag: int | Tag, entry_id: int) -> None:
        if isinstance(tag, Tag):
            tag = tag.id

        with Session(self.engine) as session, session.begin():
            meta_tag_box = session.scalars(
                select(TagBoxField).where(
                    and_(
                        TagBoxField.entry_id == entry_id,
                        TagBoxField.type == TagBoxTypes.meta_tag_box,
                    )
                )
            ).one()
            tag = session.scalars(select(Tag).where(Tag.id == tag)).one()

            meta_tag_box.tags.add(tag)

    def remove_tag_from_entry_meta_tags(self, tag: int | Tag, entry_id: int) -> None:
        if isinstance(tag, Tag):
            tag = tag.id

        with Session(self.engine) as session, session.begin():
            meta_tag_box = session.scalars(
                select(TagBoxField).where(
                    and_(
                        TagBoxField.entry_id == entry_id,
                        TagBoxField.type == TagBoxTypes.meta_tag_box,
                    )
                )
            ).one()
            tag = session.scalars(select(Tag).where(Tag.id == tag)).one()

            meta_tag_box.tags.remove(tag)

    def entry_archived_favorited_status(self, entry: int | Entry) -> tuple[bool, bool]:
        if isinstance(entry, Entry):
            entry = entry.id
        with Session(self.engine) as session, session.begin():
            entry_ = session.scalars(select(Entry).where(Entry.id == entry)).one()

            return (entry_.archived, entry_.favorited)

    def save_library_backup_to_disk(self, *args, **kwargs):
        logger.error("save_library_backup_to_disk to be implemented")

    def get_tag(self, tag_id: int) -> Tag:
        with Session(self.engine) as session, session.begin():
            tag = session.scalars(select(Tag).where(Tag.id == tag_id)).one()
            session.expunge(tag)
            return tag

    def refresh_dupe_entries(self, filename: str) -> None:
        logger.info("refreshing dupe entries", filename=filename)
        # TODO - implement this
        raise NotImplementedError

    def fix_missing_files(self) -> None:
        logger.error("fix_missing_files to be implemented")

    def refresh_dupe_files(self, filename: str):
        logger.error("refresh_dupe_files to be implemented")

    def remove_missing_files(self):
        logger.error("remove_missing_files to be implemented")

    def get_entry_id_from_filepath(self, item):
        logger.error("get_entry_id_from_filepath to be implemented")

    def mirror_entry_fields(self, items: list):
        logger.error("mirror_entry_fields to be implemented")

    def merge_dupe_entries(self):
        logger.error("merge_dupe_entries to be implemented")
