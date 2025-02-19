# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from datetime import datetime as dt
from pathlib import Path

from sqlalchemy import JSON, ForeignKey, ForeignKeyConstraint, Integer, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...constants import TAG_ARCHIVED, TAG_FAVORITE
from .db import Base, PathType
from .fields import (
    BaseField,
    BooleanField,
    DatetimeField,
    FieldTypeEnum,
    TextField,
)
from .joins import TagParent


class Namespace(Base):
    __tablename__ = "namespaces"

    namespace: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)

    def __init__(
        self,
        namespace: str,
        name: str,
    ):
        self.namespace = namespace
        self.name = name
        super().__init__()


class TagAlias(Base):
    __tablename__ = "tag_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    tag: Mapped["Tag"] = relationship(back_populates="aliases")

    def __init__(self, name: str, tag_id: int | None = None):
        self.name = name

        if tag_id is not None:
            self.tag_id = tag_id

        super().__init__()


class TagColorGroup(Base):
    __tablename__ = "tag_colors"

    slug: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    namespace: Mapped[str] = mapped_column(
        ForeignKey("namespaces.namespace"), primary_key=True, nullable=False
    )
    name: Mapped[str] = mapped_column()
    primary: Mapped[str] = mapped_column(nullable=False)
    secondary: Mapped[str | None]
    color_border: Mapped[bool] = mapped_column(nullable=False, default=False)

    # TODO: Determine if slug and namespace can be optional and generated/added here if needed.
    def __init__(
        self,
        slug: str,
        namespace: str,
        name: str,
        primary: str,
        secondary: str | None = None,
        color_border: bool = False,
    ):
        self.slug = slug
        self.namespace = namespace
        self.name = name
        self.primary = primary
        if secondary:
            self.secondary = secondary
        self.color_border = color_border
        super().__init__()


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    shorthand: Mapped[str | None]
    color_namespace: Mapped[str | None] = mapped_column()
    color_slug: Mapped[str | None] = mapped_column()
    color: Mapped[TagColorGroup | None] = relationship(lazy="joined")
    is_category: Mapped[bool]
    icon: Mapped[str | None]
    aliases: Mapped[set[TagAlias]] = relationship(back_populates="tag")
    parent_tags: Mapped[set["Tag"]] = relationship(
        secondary=TagParent.__tablename__,
        primaryjoin="Tag.id == TagParent.parent_id",
        secondaryjoin="Tag.id == TagParent.child_id",
        back_populates="parent_tags",
    )
    disambiguation_id: Mapped[int | None]

    __table_args__ = (
        ForeignKeyConstraint(
            [color_namespace, color_slug], [TagColorGroup.namespace, TagColorGroup.slug]
        ),
        {"sqlite_autoincrement": True},
    )

    @property
    def parent_ids(self) -> list[int]:
        return [tag.id for tag in self.parent_tags]

    @property
    def alias_strings(self) -> list[str]:
        return [alias.name for alias in self.aliases]

    @property
    def alias_ids(self) -> list[int]:
        return [tag.id for tag in self.aliases]

    def __init__(
        self,
        id: int | None = None,
        name: str | None = None,
        shorthand: str | None = None,
        aliases: set[TagAlias] | None = None,
        parent_tags: set["Tag"] | None = None,
        icon: str | None = None,
        color_namespace: str | None = None,
        color_slug: str | None = None,
        disambiguation_id: int | None = None,
        is_category: bool = False,
    ):
        self.name = name
        self.aliases = aliases or set()
        self.parent_tags = parent_tags or set()
        self.color_namespace = color_namespace
        self.color_slug = color_slug
        self.icon = icon
        self.shorthand = shorthand
        self.disambiguation_id = disambiguation_id
        self.is_category = is_category
        assert not self.id
        self.id = id
        super().__init__()

    def __str__(self) -> str:
        return f"<Tag ID: {self.id} Name: {self.name}>"

    def __repr__(self) -> str:
        return self.__str__()

    def __lt__(self, other) -> bool:
        return self.name < other.name

    def __le__(self, other) -> bool:
        return self.name <= other.name

    def __gt__(self, other) -> bool:
        return self.name > other.name

    def __ge__(self, other) -> bool:
        return self.name >= other.name


class Folder(Base):
    __tablename__ = "folders"

    # TODO - implement this
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[Path] = mapped_column(PathType, unique=True)
    uuid: Mapped[str] = mapped_column(unique=True)


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    folder_id: Mapped[int] = mapped_column(ForeignKey("folders.id"))
    folder: Mapped[Folder] = relationship("Folder")

    path: Mapped[Path] = mapped_column(PathType, unique=True)
    suffix: Mapped[str] = mapped_column()
    date_created: Mapped[dt | None]
    date_modified: Mapped[dt | None]
    date_added: Mapped[dt | None]

    tags: Mapped[set[Tag]] = relationship(secondary="tag_entries")

    text_fields: Mapped[list[TextField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )
    datetime_fields: Mapped[list[DatetimeField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )

    @property
    def fields(self) -> list[BaseField]:
        fields: list[BaseField] = []
        fields.extend(self.text_fields)
        fields.extend(self.datetime_fields)
        fields = sorted(fields, key=lambda field: field.type.position)
        return fields

    @property
    def is_favorite(self) -> bool:
        return any(tag.id == TAG_FAVORITE for tag in self.tags)

    @property
    def is_archived(self) -> bool:
        return any(tag.id == TAG_ARCHIVED for tag in self.tags)

    def __init__(
        self,
        path: Path,
        folder: Folder,
        fields: list[BaseField],
        id: int | None = None,
        date_created: dt | None = None,
        date_modified: dt | None = None,
        date_added: dt | None = None,
    ) -> None:
        self.path = path
        self.folder = folder
        self.id = id
        self.suffix = path.suffix.lstrip(".").lower()

        # The date the file associated with this entry was created.
        # st_birthtime on Windows and Mac, st_ctime on Linux.
        self.date_created = date_created
        # The date the file associated with this entry was last modified: st_mtime.
        self.date_modified = date_modified
        # The date this entry was added to the library.
        self.date_added = date_added

        for field in fields:
            if isinstance(field, TextField):
                self.text_fields.append(field)
            elif isinstance(field, DatetimeField):
                self.datetime_fields.append(field)
            else:
                raise ValueError(f"Invalid field type: {field}")

    def has_tag(self, tag: Tag) -> bool:
        return tag in self.tags

    def remove_tag(self, tag: Tag) -> None:
        """Removes a Tag from the Entry."""
        self.tags.remove(tag)


class ValueType(Base):
    """Define Field Types in the Library.

    Example:
        key: content_tags (this field is slugified `name`)
        name: Content Tags (this field is human readable name)
        kind: type of content (Text Line, Text Box, Tags, Datetime, Checkbox)
        is_default: Should the field be present in new Entry?
        order: position of the field widget in the Entry form

    """

    __tablename__ = "value_type"

    key: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[FieldTypeEnum] = mapped_column(default=FieldTypeEnum.TEXT_LINE)
    is_default: Mapped[bool]
    position: Mapped[int]

    # add relations to other tables
    text_fields: Mapped[list[TextField]] = relationship("TextField", back_populates="type")
    datetime_fields: Mapped[list[DatetimeField]] = relationship(
        "DatetimeField", back_populates="type"
    )
    boolean_fields: Mapped[list[BooleanField]] = relationship("BooleanField", back_populates="type")

    @property
    def as_field(self) -> BaseField:
        FieldClass = {  # noqa: N806
            FieldTypeEnum.TEXT_LINE: TextField,
            FieldTypeEnum.TEXT_BOX: TextField,
            FieldTypeEnum.DATETIME: DatetimeField,
            FieldTypeEnum.BOOLEAN: BooleanField,
        }

        return FieldClass[self.type](
            type_key=self.key,
            position=self.position,
        )


@event.listens_for(ValueType, "before_insert")
def slugify_field_key(mapper, connection, target):
    """Slugify the field key before inserting into the database."""
    if not target.key:
        from .library import slugify

        target.key = slugify(target.tag)


class Preferences(Base):
    __tablename__ = "preferences"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
