from pathlib import Path
from typing import Optional

from sqlalchemy import JSON, ForeignKey, Integer, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, PathType
from .enums import TagColor
from .fields import (
    DatetimeField,
    Field,
    TagBoxField,
    TextField,
    FieldTypeEnum,
    _FieldID,
)
from .joins import TagSubtag
from ...constants import TAG_FAVORITE, TAG_ARCHIVED


class TagAlias(Base):
    __tablename__ = "tag_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]

    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    tag: Mapped["Tag"] = relationship(back_populates="aliases")

    def __init__(self, name: str, tag: Optional["Tag"] = None):
        self.name = name

        if tag:
            self.tag = tag

        super().__init__()


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(unique=True)
    shorthand: Mapped[str | None]
    color: Mapped[TagColor]
    icon: Mapped[str | None]

    aliases: Mapped[set[TagAlias]] = relationship(back_populates="tag")

    parent_tags: Mapped[set["Tag"]] = relationship(
        secondary=TagSubtag.__tablename__,
        primaryjoin="Tag.id == TagSubtag.child_id",
        secondaryjoin="Tag.id == TagSubtag.parent_id",
        back_populates="subtags",
    )

    subtags: Mapped[set["Tag"]] = relationship(
        secondary=TagSubtag.__tablename__,
        primaryjoin="Tag.id == TagSubtag.parent_id",
        secondaryjoin="Tag.id == TagSubtag.child_id",
        back_populates="parent_tags",
    )

    @property
    def subtag_ids(self) -> list[int]:
        return [tag.id for tag in self.subtags]

    @property
    def alias_strings(self) -> list[str]:
        return [alias.name for alias in self.aliases]

    def __init__(
        self,
        name: str,
        shorthand: str | None = None,
        aliases: set[TagAlias] | None = None,
        parent_tags: set["Tag"] | None = None,
        subtags: set["Tag"] | None = None,
        icon: str | None = None,
        color: TagColor = TagColor.DEFAULT,
        id: int | None = None,
    ):
        self.name = name
        self.aliases = aliases or set()
        self.parent_tags = parent_tags or set()
        self.subtags = subtags or set()
        self.color = color
        self.icon = icon
        self.shorthand = shorthand
        assert not self.id
        self.id = id
        super().__init__()

    def __str__(self) -> str:
        return f"<Tag ID: {self.id} Name: {self.name}>"

    def __repr__(self) -> str:
        return self.__str__()


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    path: Mapped[Path] = mapped_column(PathType, unique=True)

    text_fields: Mapped[list[TextField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )
    datetime_fields: Mapped[list[DatetimeField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )
    tag_box_fields: Mapped[list[TagBoxField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )

    @property
    def fields(self) -> list[Field]:
        fields: list[Field] = []
        fields.extend(self.tag_box_fields)
        fields.extend(self.text_fields)
        fields.extend(self.datetime_fields)
        fields = sorted(fields, key=lambda field: field.type.order)
        return fields

    @property
    def tags(self) -> set[Tag]:
        tag_set: set[Tag] = set()
        for tag_box_field in self.tag_box_fields:
            tag_set.update(tag_box_field.tags)
        return tag_set

    @property
    def is_favorited(self) -> bool:
        for tag_box_field in self.tag_box_fields:
            if tag_box_field.type_key == _FieldID.TAGS_META.name:
                for tag in tag_box_field.tags:
                    if tag.id == TAG_FAVORITE:
                        return True
        return False

    @property
    def is_archived(self) -> bool:
        for tag_box_field in self.tag_box_fields:
            if tag_box_field.type_key == _FieldID.TAGS_META.name:
                for tag in tag_box_field.tags:
                    if tag.id == TAG_ARCHIVED:
                        return True
        return False

    def __init__(
        self,
        path: Path,
        fields: list[Field] | None = None,
    ) -> None:
        self.path = path

        if fields is None:
            fields = [
                TagBoxField(type_key=_FieldID.TAGS_META.name),
                TagBoxField(type_key=_FieldID.TAGS_CONTENT.name),
                TextField(type_key=_FieldID.TITLE.name),
            ]

        for field in fields:
            if isinstance(field, TextField):
                self.text_fields.append(field)
            elif isinstance(field, DatetimeField):
                self.datetime_fields.append(field)
            elif isinstance(field, TagBoxField):
                self.tag_box_fields.append(field)
            else:
                raise ValueError(f"Invalid field type: {field}")

    def has_tag(self, tag: Tag) -> bool:
        return tag in self.tags

    def remove_tag(self, tag: Tag, field: TagBoxField | None = None) -> None:
        """
        Removes a Tag from the Entry. If given a field index, the given Tag will
        only be removed from that index. If left blank, all instances of that
        Tag will be removed from the Entry.
        """
        if field:
            field.tags.remove(tag)
            return

        for tag_box_field in self.tag_box_fields:
            tag_box_field.tags.remove(tag)


class LibraryField(Base):
    """Define Field Types in the Library.

    Example:
        key: content_tags (this field is slugified `name`)
        name: Content Tags (this field is human readable name)
        kind: type of content (Text Line, Text Box, Tags, Datetime, Checkbox)

    """

    __tablename__ = "library_fields"

    key: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[FieldTypeEnum] = mapped_column(default=FieldTypeEnum.TEXT_LINE)
    order: Mapped[int] = mapped_column(default=0)

    # add relations to other tables
    text_fields: Mapped[list[TextField]] = relationship(
        "TextField", back_populates="type"
    )
    datetime_fields: Mapped[list[DatetimeField]] = relationship(
        "DatetimeField", back_populates="type"
    )
    tag_box_fields: Mapped[list[TagBoxField]] = relationship(
        "TagBoxField", back_populates="type"
    )


@event.listens_for(LibraryField, "before_insert")
def slugify_field_key(mapper, connection, target):
    """Slugify the field key before inserting into the database."""
    if not target.key:
        from .library import slugify

        target.key = slugify(target.tag)


class Preferences(Base):
    __tablename__ = "preferences"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
